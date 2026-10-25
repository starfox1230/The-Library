from __future__ import annotations

import unittest

import httpx
from openai import BadRequestError

from cursor_transcriber.openai_client import friendly_openai_error


class OpenAIErrorTests(unittest.TestCase):
    def test_bad_request_shows_details_for_sdk_unwrapped_and_wrapped_bodies(self):
        detail = "Audio file might be corrupted or unsupported"
        for body in ({"message": detail}, {"error": {"message": detail}}):
            with self.subTest(body=body):
                response = httpx.Response(400, request=httpx.Request("POST", "https://example.test"))
                error = BadRequestError("Bad request", response=response, body=body)
                self.assertEqual(friendly_openai_error(error), "OpenAI rejected the audio request: " + detail)


if __name__ == "__main__":
    unittest.main()
