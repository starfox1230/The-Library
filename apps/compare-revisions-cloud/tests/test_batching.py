"""Synthetic checks for server concurrency, streaming and batch isolation."""
import json
import threading
import unittest
from unittest.mock import patch
from test_app import import_offline_app, report


class BatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = import_offline_app()

    def setUp(self):
        self.module.auth.user = {'tid':self.module.UAB_TENANT_ID,'name':'Synthetic tester'}
        self.client = self.module.app.test_client()
        with self.client.session_transaction() as session:
            session['comparison_csrf_token'] = 'synthetic-csrf'
        self.headers = {'X-CSRF-Token':'synthetic-csrf'}
        guard = patch('socket.socket.connect',side_effect=AssertionError('No network in tests'))
        guard.start()
        self.addCleanup(guard.stop)

    def payload(self, count=2):
        return {'custom_prompt':'The complete replacement instructions.',
                'cases':[{'id':f'g{i+1}','resident_report':report(), 'attending_report':report()}
                         for i in range(count)]}

    def post(self, payload, **kwargs):
        return self.client.post('/analyze-batch',json=payload,headers=self.headers,**kwargs)

    def test_one_hundred_model_calls_start_together_and_keep_identity(self):
        barrier = threading.Barrier(100, timeout=8)
        lock = threading.Lock()
        active = peak = 0
        seen = []
        def summarize(case, instructions):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak,active)
                seen.append((case['id'],instructions))
            barrier.wait()  # A four-worker implementation cannot pass this.
            with lock:
                active -= 1
            return dict(case,status='complete',status_message='Complete')
        with patch.object(self.module,'get_azure_client',return_value=object()), \
                patch.object(self.module,'summarize_case',side_effect=summarize):
            response = self.post(self.payload(100))
            events = [json.loads(line) for line in response.data.splitlines()]
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.mimetype,'application/x-ndjson')
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertEqual(peak,100)
        results = [e for e in events if e['type']=='case']
        self.assertEqual({e['id'] for e in results},{f'g{i+1}' for i in range(100)})
        self.assertTrue(all(e['id']==e['result']['id'] for e in results))
        self.assertTrue(all(prompt==self.payload()['custom_prompt'] for _,prompt in seen))
        self.assertEqual(events[-1],{'type':'done','total':100})

    def test_first_result_is_streamed_before_slowest_case_finishes(self):
        slow_started, release = threading.Event(), threading.Event()
        def summarize(case, instructions):
            if case['id']=='g2':
                slow_started.set()
                if not release.wait(5):
                    raise AssertionError('Test did not release slower case')
            else:
                self.assertTrue(slow_started.wait(5))
            return dict(case,status='complete')
        with patch.object(self.module,'get_azure_client',return_value=object()), \
                patch.object(self.module,'summarize_case',side_effect=summarize):
            response = self.post(self.payload(),buffered=False)
            stream = iter(response.response)
            self.assertEqual(json.loads(next(stream))['type'],'started')
            try:
                first = json.loads(next(stream))
                self.assertEqual(first['id'],'g1')
                self.assertFalse(release.is_set())
            finally:
                release.set()
            rest = [json.loads(line) for line in stream]
            response.close()
        self.assertEqual(rest[0]['id'],'g2')
        self.assertEqual(rest[-1]['type'],'done')

    def test_worker_failure_preserves_other_results_and_hides_exception_text(self):
        def summarize(case, instructions):
            if case['id']=='g2':
                raise RuntimeError('private_source_sentinel')
            return dict(case,status='complete')
        with patch.object(self.module,'get_azure_client',return_value=object()), \
                patch.object(self.module,'summarize_case',side_effect=summarize), \
                self.assertLogs(self.module.logger,level='WARNING') as logs:
            response = self.post(self.payload())
            text = response.data.decode()
        results = {e['id']:e['result'] for e in map(json.loads,text.splitlines()) if e['type']=='case'}
        self.assertEqual(results['g1']['status'],'complete')
        self.assertEqual(results['g2']['status'],'error')
        self.assertNotIn('private_source_sentinel',text+str(logs.output))

    def test_invalid_or_duplicate_case_rejects_whole_batch_before_calls(self):
        invalid = [self.payload(101), self.payload(0)]
        duplicate = self.payload(); duplicate['cases'][1]['id']='g1'; invalid.append(duplicate)
        bad = self.payload();bad['cases'][1]['resident_report']=None;invalid.append(bad)
        blank = self.payload();blank['custom_prompt']=' ';invalid.append(blank)
        oversized = self.payload();oversized['custom_prompt']='x'*40001;invalid.append(oversized)
        with patch.object(self.module,'get_azure_client',side_effect=AssertionError('No call')), \
                patch.object(self.module,'summarize_case',side_effect=AssertionError('No call')):
            for payload in invalid:
                with self.subTest(count=len(payload['cases'])):
                    self.assertEqual(self.post(payload).status_code,400)

    def test_missing_capture_is_returned_without_model_call(self):
        payload = self.payload(1);payload['cases'][0]['attending_report']=''
        with patch.object(self.module,'get_azure_client',side_effect=AssertionError('No client')), \
                patch.object(self.module,'summarize_case',side_effect=AssertionError('No call')):
            events = [json.loads(line) for line in self.post(payload).data.splitlines()]
        self.assertEqual(events[1]['result']['status'],'unavailable')
        self.assertEqual(events[-1]['type'],'done')

    def test_initialization_failure_returns_recoverable_results_for_all_cases(self):
        with patch.object(self.module,'get_azure_client',side_effect=RuntimeError('private_key_sentinel')), \
                self.assertLogs(self.module.logger,level='WARNING') as logs:
            text = self.post(self.payload()).data.decode()
        events = [json.loads(line) for line in text.splitlines()]
        self.assertEqual(sum(e['type']=='case' and e['result']['status']=='error' for e in events),2)
        self.assertNotIn('private_key_sentinel',text+str(logs.output))
        self.assertEqual(events[-1]['type'],'done')

    def test_batch_route_requires_login_correct_tenant_and_csrf(self):
        self.assertEqual(self.client.post('/analyze-batch',json=self.payload()).status_code,400)
        self.module.auth.user={'tid':'wrong-tenant'}
        self.assertEqual(self.post(self.payload()).status_code,403)
        self.module.auth.user=None
        self.assertEqual(self.post(self.payload()).status_code,401)

    def test_request_byte_limit_still_rejects_before_model_calls(self):
        with patch.object(self.module,'get_azure_client',side_effect=AssertionError('No call')):
            response = self.client.post('/analyze-batch',data='x'*(5*1024*1024+1),
                content_type='application/json',headers=self.headers)
        self.assertEqual(response.status_code,413)

    def test_rate_limit_is_reported_without_leaking_provider_error(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        client=MagicMock()
        client.responses.create.side_effect=self.module.RateLimitError('private_provider_sentinel',
            response=SimpleNamespace(status_code=429,headers={},request=SimpleNamespace(method='POST',url='https://synthetic.invalid')),
            body={'private':'private_provider_sentinel'})
        case=self.module.prepare_cases('Case 1\nAttending Report:\n'+report()+'\nResident Report:\n'+report())[0]
        with patch.object(self.module,'get_azure_client',return_value=client), \
                self.assertLogs(self.module.logger,level='WARNING') as logs:
            result=self.module.summarize_case(case)
        self.assertEqual(result['status'],'error')
        self.assertIn('request rate or available quota',result['status_message'])
        self.assertNotIn('private_provider_sentinel',str(result)+str(logs.output))


if __name__=='__main__':
    unittest.main()
