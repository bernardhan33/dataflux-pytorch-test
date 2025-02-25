"""
 Copyright 2023 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 """

import unittest
from unittest import mock

from dataflux_client_python.dataflux_core.tests import fake_gcs
from dataflux_pytorch import dataflux_mapstyle_dataset


class ListingTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.project_name = "foo"
        self.bucket_name = "bar"
        self.config = dataflux_mapstyle_dataset.Config(
            num_processes=3, max_listing_retries=3, prefix="prefix/"
        )
        self.data_format_fn = lambda data: data
        client = fake_gcs.Client()

        self.want_objects = [("objectA", 1), ("objectB", 2)]
        self.storage_client = client

    @mock.patch("dataflux_pytorch.dataflux_mapstyle_dataset.dataflux_core")
    def test_init(self, mock_dataflux_core):
        """Tests the DataFluxMapStyleDataset can be initiated with the expected listing results."""
        # Arrange.
        mock_listing_controller = mock.Mock()
        mock_listing_controller.run.return_value = self.want_objects
        mock_dataflux_core.fast_list.ListingController.return_value = (
            mock_listing_controller
        )

        # Act.
        ds = dataflux_mapstyle_dataset.DataFluxMapStyleDataset(
            project_name=self.project_name,
            bucket_name=self.bucket_name,
            config=self.config,
            data_format_fn=self.data_format_fn,
            storage_client=self.storage_client,
        )

        # Assert.
        self.assertEqual(
            ds.objects,
            self.want_objects,
            f"got listed objects {ds.objects}, want {self.want_objects}",
        )

    @mock.patch("dataflux_pytorch.dataflux_mapstyle_dataset.dataflux_core")
    def test_init_with_required_parameters(self, mock_dataflux_core):
        """Tests the DataFluxMapStyleDataset can be initiated with only the required parameters."""
        # Arrange.
        mock_listing_controller = mock.Mock()
        mock_listing_controller.run.return_value = self.want_objects
        mock_dataflux_core.fast_list.ListingController.return_value = (
            mock_listing_controller
        )

        # Act.
        ds = dataflux_mapstyle_dataset.DataFluxMapStyleDataset(
            project_name=self.project_name,
            bucket_name=self.bucket_name,
            # storage_client is optional param but still needed here
            # to avoid actual storage.Client construction.
            storage_client=self.storage_client,
        )

        # Assert.
        self.assertEqual(
            ds.objects,
            self.want_objects,
            f"got listed objects {ds.objects}, want {self.want_objects}",
        )

    @mock.patch("dataflux_pytorch.dataflux_mapstyle_dataset.dataflux_core")
    def test_init_retry_exception_passes(self, mock_dataflux_core):
        """Tests that the initialization retries objects llisting upon exception and passes."""
        # Arrange.
        mock_listing_controller = mock.Mock()

        # Simulate that the first invocation raises an exception and the second invocation
        # passes with the wanted results.
        mock_listing_controller.run.side_effect = [
            Exception(),
            self.want_objects,
            Exception(),
        ]
        mock_dataflux_core.fast_list.ListingController.return_value = (
            mock_listing_controller
        )

        # Act.
        ds = dataflux_mapstyle_dataset.DataFluxMapStyleDataset(
            project_name=self.project_name,
            bucket_name=self.bucket_name,
            config=self.config,
            data_format_fn=self.data_format_fn,
            storage_client=self.storage_client,
        )

        # Assert.
        self.assertEqual(
            ds.objects,
            self.want_objects,
            f"got listed objects {ds.objects}, want {self.want_objects}",
        )

    @mock.patch("dataflux_pytorch.dataflux_mapstyle_dataset.dataflux_core")
    def test_init_raises_exception_when_retries_exhaust(self, mock_dataflux_core):
        """Tests that the initialization raises exception upon exhaustive retries."""
        # Arrange.
        mock_listing_controller = mock.Mock()
        want_exception = RuntimeError("123")

        # Simulate that all retries return with exceptions.
        mock_listing_controller.run.side_effect = [
            want_exception for _ in range(self.config.max_listing_retries)
        ]
        mock_dataflux_core.fast_list.ListingController.return_value = (
            mock_listing_controller
        )

        # Act & Assert.
        with self.assertRaises(RuntimeError) as re:
            ds = dataflux_mapstyle_dataset.DataFluxMapStyleDataset(
                project_name=self.project_name,
                bucket_name=self.bucket_name,
                config=self.config,
                data_format_fn=self.data_format_fn,
                storage_client=self.storage_client,
            )
            self.assertIsNone(
                ds.objects,
                f"got a non-None objects instance variable, want None when all listing retries are exhausted",
            )

        self.assertEqual(
            re.exception,
            want_exception,
            f"got exception {re.exception}, want {want_exception}",
        )

    @mock.patch("dataflux_pytorch.dataflux_mapstyle_dataset.dataflux_core")
    def test_len(self, mock_dataflux_core):
        """Tests that the len(dataset) method returns the correct number of listed objects."""
        # Arrange.
        mock_listing_controller = mock.Mock()
        mock_listing_controller.run.return_value = self.want_objects
        mock_dataflux_core.fast_list.ListingController.return_value = (
            mock_listing_controller
        )

        # Act.
        ds = dataflux_mapstyle_dataset.DataFluxMapStyleDataset(
            project_name=self.project_name,
            bucket_name=self.bucket_name,
            config=self.config,
            data_format_fn=self.data_format_fn,
            storage_client=self.storage_client,
        )

        # Assert.
        self.assertEqual(
            len(ds),
            len(self.want_objects),
            f"got len(ds)={len(ds)}, want {len(self.want_objects)}",
        )

    @mock.patch("dataflux_pytorch.dataflux_mapstyle_dataset.dataflux_core")
    def test_getitem(self, mock_dataflux_core):
        """Tests that the dataset[idx] method returns the correct downloaded object content."""
        # Arrange.
        mock_listing_controller = mock.Mock()
        mock_listing_controller.run.return_value = self.want_objects
        mock_dataflux_core.fast_list.ListingController.return_value = (
            mock_listing_controller
        )
        want_downloaded = bytes("content", "utf-8")
        mock_dataflux_core.download.download_single.return_value = want_downloaded
        want_idx = 0

        # Act.
        ds = dataflux_mapstyle_dataset.DataFluxMapStyleDataset(
            project_name=self.project_name,
            bucket_name=self.bucket_name,
            config=self.config,
            data_format_fn=self.data_format_fn,
            storage_client=self.storage_client,
        )
        got_downloaded = ds[want_idx]

        # Assert.
        self.assertEqual(
            got_downloaded,
            want_downloaded,
        )
        mock_dataflux_core.download.download_single.assert_called_with(
            storage_client=self.storage_client,
            bucket_name=self.bucket_name,
            object_name=self.want_objects[want_idx][0],
        )

    @mock.patch("dataflux_pytorch.dataflux_mapstyle_dataset.dataflux_core")
    def test_getitems(self, mock_dataflux_core):
        """Tests that the dataset.__getitems__ method returns the list of the correct downloaded object content."""
        # Arrange.
        mock_listing_controller = mock.Mock()
        mock_listing_controller.run.return_value = self.want_objects
        mock_dataflux_core.fast_list.ListingController.return_value = (
            mock_listing_controller
        )
        want_optimization_params = object()
        mock_dataflux_core.download.DataFluxDownloadOptimizationParams.return_value = (
            want_optimization_params
        )
        dataflux_download_return_val = [
            bytes("contentA", "utf-8"),
            bytes("contentBB", "utf-8"),
        ]
        mock_dataflux_core.download.dataflux_download.return_value = (
            dataflux_download_return_val
        )
        data_format_fn = lambda content: len(content)
        want_downloaded = [
            data_format_fn(bytes_content)
            for bytes_content in dataflux_download_return_val
        ]
        want_indices = [0, 1]

        # Act.
        ds = dataflux_mapstyle_dataset.DataFluxMapStyleDataset(
            project_name=self.project_name,
            bucket_name=self.bucket_name,
            config=self.config,
            data_format_fn=data_format_fn,
            storage_client=self.storage_client,
        )
        got_downloaded = ds.__getitems__(want_indices)

        # Assert.
        self.assertEqual(
            got_downloaded,
            want_downloaded,
        )
        mock_dataflux_core.download.dataflux_download.assert_called_with(
            project_name=self.project_name,
            bucket_name=self.bucket_name,
            objects=self.want_objects,
            storage_client=self.storage_client,
            dataflux_download_optimization_params=want_optimization_params,
        )


if __name__ == "__main__":
    unittest.main()
