import unittest

from threads_client import ThreadsAPIError, ThreadsClient


class FakeResponse:
    def __init__(self, payload, ok=True, status_code=200):
        self.payload = payload
        self.ok = ok
        self.status_code = status_code

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


class ThreadsClientTests(unittest.TestCase):
    def test_publishes_text_in_two_steps(self) -> None:
        session = FakeSession(
            [FakeResponse({"id": "container-123"}), FakeResponse({"id": "thread-456"})]
        )
        client = ThreadsClient("secret-token", session=session)

        thread_id = client.publish_text("Daily summary")

        self.assertEqual(thread_id, "thread-456")
        self.assertEqual(
            session.calls[0][0],
            "https://graph.threads.com/me/threads",
        )
        self.assertEqual(
            session.calls[0][1]["data"],
            {"media_type": "TEXT", "text": "Daily summary"},
        )
        self.assertEqual(
            session.calls[1][0],
            "https://graph.threads.com/me/threads_publish",
        )
        self.assertEqual(
            session.calls[1][1]["data"],
            {"creation_id": "container-123"},
        )
        self.assertEqual(
            session.calls[0][1]["headers"]["Authorization"],
            "Bearer secret-token",
        )

    def test_surfaces_api_error_without_token(self) -> None:
        session = FakeSession(
            [
                FakeResponse(
                    {"error": {"message": "Invalid OAuth access token"}},
                    ok=False,
                    status_code=401,
                )
            ]
        )
        client = ThreadsClient("secret-token", session=session)

        with self.assertRaisesRegex(
            ThreadsAPIError,
            "Invalid OAuth access token",
        ):
            client.create_text_container("Daily summary")

        self.assertNotIn("secret-token", str(session.responses))

    def test_rejects_empty_post(self) -> None:
        client = ThreadsClient("secret-token", session=FakeSession([]))
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            client.create_text_container("   ")


if __name__ == "__main__":
    unittest.main()
