import os
import numpy as np
from unittest.mock import patch,Mock
import pytest

class Target:
    value = None

@patch.object(Target,'value',new=np.array([-5.5,3.0]))
def test_array_replacement():
    assert (Target.value==np.array([-5.5,3.0])).all()

@patch.object(Target,'value')
def test_default_mock_injection(mock_getcwd):
    mock_getcwd.return_value='owned';assert Target.value()=='owned'

@patch.object(Target,'value',new=Mock(return_value='explicit'))
def test_explicit_mock_no_injection():
    assert Target.value()=='explicit'

@pytest.fixture
def ordinary_fixture():return 37

@patch.object(Target,'value')
def test_default_mock_and_fixture(mock_getcwd,ordinary_fixture):
    assert ordinary_fixture==37;assert mock_getcwd is Target.value

def test_plain_function():assert 2+2==4
