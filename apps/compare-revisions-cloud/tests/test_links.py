"""Exact, section-scoped browser offsets using synthetic reports only."""
import unittest
from test_app import import_offline_app, report, pasted_case


def utf16_slice(text, start, end):
    return text.encode('utf-16-le')[start * 2:end * 2].decode('utf-16-le')


class LinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = import_offline_app()

    def parsed(self, resident, attending=None):
        return {side: self.m.parse_sections(text, side) for side, text in
                [('resident', resident), ('attending', attending or resident)]}

    def item(self, **changes):
        value = dict(importance='minor', resident_section='r0', resident_quote='Clear lungs.',
                     attending_section='', attending_quote='', major_evidence_side='none',
                     major_evidence_section='', major_evidence_quote='')
        value.update(changes)
        return value

    def test_same_words_in_impression_are_not_linked_by_findings_evidence(self):
        parsed = self.parsed(report('Clear lungs.', 'Clear lungs.'))
        links = self.m.link_revision_sources(self.item(), parsed)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]['section'], 'r0')
        self.assertEqual(links[0]['start'], self.m.utf16_length('FINDINGS:\n'))

    def test_all_same_section_repetitions_are_retained(self):
        parsed = self.parsed(report('Clear lungs. More detail. Clear lungs.', 'Clear lungs.'))
        links = self.m.link_revision_sources(self.item(), parsed)
        self.assertEqual(len(links), 2)
        self.assertEqual([utf16_slice(parsed['resident']['clinical_text'], l['start'], l['end'])
                          for l in links], ['Clear lungs.', 'Clear lungs.'])

    def test_major_impression_anchor_is_added_and_duplicate_evidence_is_deduplicated(self):
        parsed = self.parsed(report('Clear lungs.', 'Clear lungs.'))
        item = self.item(importance='major', major_evidence_side='resident',
                         major_evidence_section='r1', major_evidence_quote='Clear lungs.')
        links = self.m.link_revision_sources(item, parsed)
        self.assertEqual([l['kind'] for l in links], ['findings', 'impression'])
        item.update(major_evidence_section='r0')
        self.assertEqual(len(self.m.link_revision_sources(item, parsed)), 1)

    def test_astral_unicode_offsets_match_javascript_and_joined_sections(self):
        parsed = self.parsed(report('Synthetic 🧪 marker. Clear lungs.', 'New 🧪 finding.'))
        item = self.item(resident_section='r1', resident_quote='finding.')
        link = self.m.link_revision_sources(item, parsed)[0]
        self.assertEqual(utf16_slice(parsed['resident']['clinical_text'], link['start'], link['end']), 'finding.')
        self.assertEqual(link['start'], self.m.utf16_length('FINDINGS:\nSynthetic 🧪 marker. Clear lungs.\n\nIMPRESSION:\nNew 🧪 '))

    def test_missing_side_or_invalid_section_never_invents_an_anchor(self):
        parsed = self.parsed(report())
        self.assertEqual(self.m.link_revision_sources(self.item(resident_section='r9'), parsed), [])
        self.assertEqual(self.m.link_revision_sources(self.item(resident_quote='not present'), parsed), [])
        links = self.m.link_revision_sources(self.item(resident_quote='', attending_section='a0',
                                                       attending_quote='Clear lungs.'), parsed)
        self.assertEqual([l['side'] for l in links], ['attending'])

    def test_diff_runs_reconstruct_each_source_with_correct_unicode_offsets(self):
        resident = report('🧪 Clear lungs. Original detail.', 'No acute abnormality.')
        attending = report('🧪 Clear lungs. Added detail.', 'New conclusion.')
        case = self.m.prepare_cases(pasted_case(1, resident, attending))[0]
        for side, exclude, text in [('resident', 'insert', resident), ('attending', 'delete', attending)]:
            source = self.m.parse_sections(text, side)['clinical_text']
            reconstructed = ''
            for run in case['clinical_diff']:
                if run['kind'] == exclude:
                    self.assertIsNone(run[side + '_start'])
                    continue
                self.assertEqual(run[side + '_start'], self.m.utf16_length(reconstructed))
                reconstructed += run['text']
            self.assertEqual(reconstructed, source)

    def test_combined_section_and_multirun_quote_have_exact_coordinates(self):
        parsed = self.parsed('FINDINGS/IMPRESSION:\nSmall effusion. Clear lungs.')
        link = self.m.link_revision_sources(self.item(resident_quote='Small effusion. Clear lungs.'), parsed)[0]
        self.assertEqual(link['kind'], 'combined')
        prefix = self.m.utf16_length('FINDINGS/IMPRESSION:\n')
        self.assertEqual(link['start'], prefix)
        self.assertEqual(link['end'], prefix + self.m.utf16_length('Small effusion. Clear lungs.'))

    def test_displayed_headings_preserve_actual_names_and_are_not_model_evidence(self):
        text = 'EXAM: Synthetic\nFinding / Conclusion:\nBody text.\nCONCLUSIONS\nFinal text.\nCOMMUNICATION: Footer.'
        parsed = self.m.parse_sections(text)
        self.assertEqual(parsed['clinical_text'], 'Finding / Conclusion:\nBody text.\n\nCONCLUSIONS\nFinal text.')
        self.assertEqual([h['text'] for h in parsed['headings']], ['Finding / Conclusion:', 'CONCLUSIONS'])
        self.assertEqual([s['text'] for s in parsed['sections']], ['Body text.', 'Final text.'])
        self.assertEqual(self.m.link_revision_sources(self.item(resident_quote='Finding / Conclusion:'), self.parsed(text)), [])

    def test_changed_heading_names_reconstruct_both_source_structures(self):
        resident = 'FINDINGS:\nClear lungs.\nCONCLUSION:\nNo acute abnormality.'
        attending = 'FINDINGS:\nClear lungs.\nIMPRESSION:\nNo acute abnormality.'
        case = self.m.prepare_cases(pasted_case(1,resident,attending))[0]
        self.assertEqual([h['text'] for h in case['clinical_headings']['resident']], ['FINDINGS:', 'CONCLUSION:'])
        self.assertEqual([h['text'] for h in case['clinical_headings']['attending']], ['FINDINGS:', 'IMPRESSION:'])
        for side, exclude, text in [('resident','insert',resident),('attending','delete',attending)]:
            self.assertEqual(''.join(t['text'] for t in case['clinical_diff'] if t['kind']!=exclude), self.m.parse_sections(text,side)['clinical_text'])
            for h in case['clinical_headings'][side]:
                self.assertEqual(utf16_slice(self.m.parse_sections(text,side)['clinical_text'],h['start'],h['end']),h['text'])


if __name__ == '__main__':
    unittest.main()
