from unittest.mock import patch, mock_open
import unittest
from sync_labels import apply_labels


class TestApplyLabels(unittest.TestCase):

    @patch('sync_labels.client')
    @patch('sync_labels.config')
    def test_apply_labels(self, mock_config, mock_client):
        # Setup
        mock_namespace = mock_client.CoreV1Api().read_namespace.return_value
        mock_namespace.metadata.labels = {
            "pod-security.kubernetes.io/audit": "baseline",
            "pod-security.kubernetes.io/enforce": "baseline",
            "pod-security.kubernetes.io/warn": "baseline",
            "other-label": "value"
        }
        mock_namespace.name = "namespace1"

        # Mocking file read
        with patch('builtins.open', mock_open(
                read_data='{"namespace1": {"pod-security.kubernetes.io/audit": "baseline","pod-security.kubernetes.io/warn": "baseline"}}')):
            # Run the function
            apply_labels()

            # Check if the required methods were called
            mock_client.CoreV1Api().read_namespace.assert_called_with(name='namespace1')
            mock_client.CoreV1Api().patch_namespace.assert_called()
            self.assertEqual(mock_client.CoreV1Api().patch_namespace.call_count, 1)

            # Capture and log the call arguments
            args, kwargs = mock_client.CoreV1Api().patch_namespace.call_args
            print(kwargs)

            # Assertions
            if 'body' in kwargs:
                patched_body = kwargs['body']
                self.assertEqual(patched_body, {
                    'metadata': {'labels': {'pod-security.kubernetes.io/warn': 'baseline',
                                            'pod-security.kubernetes.io/audit': 'baseline', 'other-label': 'value'}}
                })
            else:
                self.fail("Body keyword argument missing in patch_namespace call.")


if __name__ == '__main__':
    unittest.main()
