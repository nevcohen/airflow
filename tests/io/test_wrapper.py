# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

from airflow.datasets import Dataset
from airflow.io.path import ObjectStoragePath
from airflow.lineage import hook


@pytest.fixture(autouse=True)
def clean_lineage_collector():
    hook._hook_lineage_collector = None
    hook._hook_lineage_collector = hook.HookLineageCollector()
    yield
    hook._hook_lineage_collector = None


@patch("airflow.providers_manager.ProvidersManager")
def test_wrapper_catches_reads_writes(providers_manager):
    providers_manager.return_value.dataset_factories.get.return_value = lambda x: Dataset(uri=x)
    uri = f"file:///tmp/{str(uuid.uuid4())}"
    path = ObjectStoragePath(uri)
    file = path.open("w")
    file.write("aaa")
    file.close()

    assert len(hook.get_hook_lineage_collector().outputs) == 1
    assert hook.get_hook_lineage_collector().outputs[0] == Dataset(uri=uri)

    file = path.open("r")
    file.read()
    file.close()

    path.unlink(missing_ok=True)

    assert len(hook.get_hook_lineage_collector().inputs) == 1
    assert hook.get_hook_lineage_collector().outputs[0] == Dataset(uri=uri)


@patch("airflow.providers_manager.ProvidersManager")
def test_wrapper_works_with_contextmanager(providers_manager):
    providers_manager.return_value.dataset_factories.get.return_value = lambda x: Dataset(uri=x)
    uri = f"file:///tmp/{str(uuid.uuid4())}"
    path = ObjectStoragePath(uri)
    with path.open("w") as file:
        file.read()
    path.unlink(missing_ok=True)

    assert len(hook.get_hook_lineage_collector().outputs) == 1
    assert hook.get_hook_lineage_collector().outputs[0] == Dataset(uri=uri)
