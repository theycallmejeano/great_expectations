import logging
import os
import shutil
from typing import List

import nbformat
from nbconvert.preprocessors import CellExecutionError, ExecutePreprocessor
from nbformat import NotebookNode

from great_expectations.data_context.util import file_relative_path
from great_expectations.exceptions.exceptions import GreatExpectationsError

logger = logging.getLogger(__name__)


def clean_up_test_files(base_dir: str, paths: List[str]) -> None:
    """
    Helper method to clean-up the files created by tests
    Args:
        base_dir str: tmp path created by the test
        paths List(str): paths or directories to delete
    """
    for path in paths:
        full_path: str = os.path.join(base_dir, path)
        if not os.path.exists(full_path):
            continue
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)


def test_run_rbp_notebook(tmp_path):
    """
    What does this test and why?

    One of the resources we have for RuleBaseProfiler is a Jupyter notebook that explains/shows the components in code.

    This test ensures the codepaths and examples described in the Notebook actually run and pass, nbconvert's
    `preprocess` function.

    """
    base_dir: str = file_relative_path(
        __file__, "../../../test_fixtures/rule_based_profiler/example_notebooks"
    )
    notebook_path: str = os.path.join(
        base_dir, "BasicExample_RBP_Instantiation_and_running.ipynb"
    )

    # temporary output notebook for traceback and debugging
    output_notebook_path: str = os.path.join(
        tmp_path, "BasicExample_RBP_Instantiation_and_running_executed.ipynb"
    )

    with open(notebook_path) as f:
        nb: NotebookNode = nbformat.read(f, as_version=4)

    ep: ExecutePreprocessor = ExecutePreprocessor(timeout=30, kernel_name="python3")

    try:
        ep.preprocess(nb, {"metadata": {"path": base_dir}})
    except CellExecutionError:
        msg: str = f'Error executing the notebook "{notebook_path}".\n\n'
        msg += f'See notebook "{output_notebook_path}" for the traceback.'
        raise GreatExpectationsError(msg)
    finally:
        with open(output_notebook_path, mode="w", encoding="utf-8") as f:
            nbformat.write(nb, f)

        paths_to_clean_up: List[str] = [
            "great_expectations/expectations/tmp",
            "great_expectations/expectations/.ge_store_backend_id",
        ]
        clean_up_test_files(base_dir=base_dir, paths=paths_to_clean_up)


def test_run_data_assistants_notebook(tmp_path):
    """
    What does this test and why?

    One of the resources we have for DataAssistants is a Jupyter notebook that explains/shows the components in code.

    This test ensures the codepaths and examples described in the Notebook actually run and pass, nbconvert's
    `preprocess` function.
    """
    base_dir: str = file_relative_path(
        __file__, "../../../test_fixtures/rule_based_profiler/example_notebooks"
    )
    notebook_path: str = os.path.join(
        base_dir, "DataAssistants_Instantiation_And_Running.ipynb"
    )
    # temporary output notebook for traceback and debugging
    output_notebook_path: str = os.path.join(
        tmp_path, "DataAssistants_Instantiation_and_running_executed.ipynb"
    )

    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)

    ep: ExecutePreprocessor = ExecutePreprocessor(timeout=30, kernel_name="python3")

    try:
        ep.preprocess(nb, {"metadata": {"path": base_dir}})
    except CellExecutionError:
        msg: str = f'Error executing the notebook "{notebook_path}".\n\n'
        msg += f'See notebook "{output_notebook_path}" for the traceback.'
        raise GreatExpectationsError(msg)
    finally:
        with open(output_notebook_path, mode="w", encoding="utf-8") as f:
            nbformat.write(nb, f)

        paths_to_clean_up: List[str] = [
            "great_expectations/expectations/tmp",
            "great_expectations/expectations/.ge_store_backend_id",
            "great_expectations/expectations/taxi_data_suite.json",
        ]
        clean_up_test_files(base_dir=base_dir, paths=paths_to_clean_up)


def test_run_self_initializing_expectations_notebook(tmp_path):
    """
    What does this test and why?
    One of the resources we have for self-initializing Expectations is a Jupyter notebook that explains/shows the
    components in code.  This test ensures the codepaths and examples described in the Notebook actually run and pass,
    nbconvert's `preprocess` function.
    """
    base_dir: str = file_relative_path(
        __file__, "../../../test_fixtures/rule_based_profiler/example_notebooks"
    )
    notebook_path: str = os.path.join(base_dir, "SelfInitializingExpectations.ipynb")
    # temporary output notebook for traceback and debugging
    output_notebook_path: str = os.path.join(
        tmp_path, "SelfInitializingExpectations_executed.ipynb"
    )

    with open(notebook_path) as f:
        nb: NotebookNode = nbformat.read(f, as_version=4)

    ep = ExecutePreprocessor(timeout=30, kernel_name="python3")

    try:
        ep.preprocess(nb, {"metadata": {"path": base_dir}})
    except CellExecutionError:
        msg = f'Error executing the notebook "{notebook_path}".\n\n'
        msg += f'See notebook "{output_notebook_path}" for the traceback.'
        raise GreatExpectationsError(msg)
    finally:
        with open(output_notebook_path, mode="w", encoding="utf-8") as f:
            nbformat.write(nb, f)

        paths_to_clean_up: List[str] = [
            "great_expectations/expectations/tmp",
            "great_expectations/expectations/.ge_store_backend_id",
            "great_expectations/expectations/new_expectation_suite.json",
        ]
        clean_up_test_files(base_dir=base_dir, paths=paths_to_clean_up)


def test_run_multibatch_inferred_asset_example(tmp_path):
    """
    What does this test and why?
    One of the resources we have for multi-batch Expectations is a Jupyter notebook that explains/shows the components
    in code. This test ensures the codepaths and examples described in the Notebook actually run and pass, nbconvert's
    `preprocess` function.
    """
    base_dir: str = file_relative_path(
        __file__, "../../../test_fixtures/rule_based_profiler/example_notebooks"
    )
    notebook_path: str = os.path.join(
        base_dir, "MultiBatchExample_InferredAssetFileSystemExample.ipynb"
    )
    # temporary output notebook for traceback and debugging
    output_notebook_path: str = os.path.join(
        tmp_path, "MultiBatchExample_InferredAssetFileSystemExample_executed.ipynb"
    )

    with open(notebook_path) as f:
        nb: NotebookNode = nbformat.read(f, as_version=4)

    ep: ExecutePreprocessor = ExecutePreprocessor(timeout=60, kernel_name="python3")

    try:
        ep.preprocess(nb, {"metadata": {"path": base_dir}})
    except CellExecutionError:
        msg: str = f'Error executing the notebook "{notebook_path}".\n\n'
        msg += f'See notebook "{output_notebook_path}" for the traceback.'
        raise GreatExpectationsError(msg)
    finally:
        with open(output_notebook_path, mode="w", encoding="utf-8") as f:
            nbformat.write(nb, f)

        paths_to_clean_up: List[str] = [
            "great_expectations/expectations/tmp",
            "great_expectations/expectations/.ge_store_backend_id",
            "great_expectations/expectations/example_inferred_suite.json",
            "great_expectations/checkpoints/my_checkpoint.yml",
            "great_expectations/uncommitted/data_docs",
            "great_expectations/uncommitted/validations/example_inferred_suite",
        ]
        clean_up_test_files(base_dir=base_dir, paths=paths_to_clean_up)


def test_run_multibatch_configured_asset_example(tmp_path):
    """
    What does this test and why?
    One of the resources we have for multi-batch Expectations is a Jupyter notebook that explains/shows the components
    in code. This test ensures the codepaths and examples described in the Notebook actually run and pass, nbconvert's
    `preprocess` function.
    """
    base_dir: str = file_relative_path(
        __file__, "../../../test_fixtures/rule_based_profiler/example_notebooks"
    )
    notebook_path: str = os.path.join(
        base_dir, "MultiBatchExample_ConfiguredAssetFileSystemExample.ipynb"
    )
    # temporary output notebook for traceback and debugging
    output_notebook_path: str = os.path.join(
        tmp_path, "MultiBatchExample_ConfiguredAssetFileSystemExample_executed.ipynb"
    )

    with open(notebook_path) as f:
        nb: NotebookNode = nbformat.read(f, as_version=4)

    ep: ExecutePreprocessor = ExecutePreprocessor(timeout=30, kernel_name="python3")

    try:
        ep.preprocess(nb, {"metadata": {"path": base_dir}})
    except CellExecutionError:
        msg: str = f'Error executing the notebook "{notebook_path}".\n\n'
        msg += f'See notebook "{output_notebook_path}" for the traceback.'
        raise GreatExpectationsError(msg)
    finally:
        with open(output_notebook_path, mode="w", encoding="utf-8") as f:
            nbformat.write(nb, f)

        paths_to_clean_up: List[str] = [
            "great_expectations/expectations/tmp",
            "great_expectations/expectations/.ge_store_backend_id",
            "great_expectations/expectations/example_configured_suite.json",
            "great_expectations/checkpoints/my_checkpoint.yml",
            "great_expectations/uncommitted/data_docs",
            "great_expectations/uncommitted/validations/example_configured_suite",
        ]
        clean_up_test_files(base_dir=base_dir, paths=paths_to_clean_up)


def test_run_multibatch_sql_asset_example(tmp_path):
    """
    What does this test and why?
    One of the resources we have for multi-batch Expectations is a Jupyter notebook that explains/shows the components
    in code. This test ensures the codepaths and examples described in the Notebook actually run and pass, nbconvert's
    `preprocess` function.
    """
    base_dir: str = file_relative_path(
        __file__, "../../../test_fixtures/rule_based_profiler/example_notebooks"
    )
    notebook_path: str = os.path.join(base_dir, "MultiBatchExample_SqlExample.ipynb")
    # temporary output notebook for traceback and debugging
    output_notebook_path: str = os.path.join(
        tmp_path, "MultiBatchExample_SqlExample_executed.ipynb"
    )
    with open(notebook_path) as f:
        nb: NotebookNode = nbformat.read(f, as_version=4)

    ep: ExecutePreprocessor = ExecutePreprocessor(timeout=30, kernel_name="python3")

    try:
        ep.preprocess(nb, {"metadata": {"path": base_dir}})
    except CellExecutionError:
        msg: str = f'Error executing the notebook "{notebook_path}".\n\n'
        msg += f'See notebook "{output_notebook_path}" for the traceback.'
        raise GreatExpectationsError(msg)
    finally:
        with open(output_notebook_path, mode="w", encoding="utf-8") as f:
            nbformat.write(nb, f)

        paths_to_clean_up: List[str] = [
            "great_expectations/expectations/tmp",
            "great_expectations/expectations/.ge_store_backend_id",
            "great_expectations/expectations/example_sql_suite.json",
            "great_expectations/checkpoints/my_checkpoint.yml",
            "great_expectations/uncommitted/data_docs",
            "great_expectations/uncommitted/validations/example_sql_suite",
        ]
        clean_up_test_files(base_dir=base_dir, paths=paths_to_clean_up)
