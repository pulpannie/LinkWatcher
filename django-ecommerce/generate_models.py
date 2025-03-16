# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import importlib
import sys
from pathlib import Path

from django.urls import path
from types import ModuleType


# Make sure we're able to import dependencies in 'pyre-check' repo, since they
# are not currently in the PyPI package for pyre-check
current_file: Path = Path(__file__).absolute()
#sys.path.append(str(current_file.parents[4]))

# Work around '-' in the name of 'pyre-check'
generate_taint_models: ModuleType = importlib.import_module(
    "env.lib.pyre_check.tools.generate_taint_models"
)
view_generator: ModuleType = importlib.import_module(
    "env.lib.pyre_check.tools.generate_taint_models.view_generator"
)
generator_specifications: ModuleType = importlib.import_module(
    "env.lib.pyre_check.tools.generate_taint_models.generator_specifications"
)

class Ignore:
    pass


def main() -> None:
    # Here, specify all the generators that you might want to call.
    generators = {
        "django_path_params": generate_taint_models.RESTApiSourceGenerator(
            django_urls=view_generator.DjangoUrls(
                urls_module="core.urls",
                url_pattern_type=path,
                url_resolver_type=Ignore,
            )
        )
      #   "decorator_extracted_params": generate_taint_models.AnnotatedFreeFunctionWithDecoratorGenerator(
      #       root=".",
      #       annotation_specifications=[
      #           generate_taint_models.DecoratorAnnotationSpecification(
      #               decorator="@api_wrapper",
      #               annotations=generator_specifications.default_entrypoint_taint,
      #           )
      #       ],
      #   ),
    }
    # The `run_generators` function will take care of parsing command-line arguments, as
    # well as executing the generators specified in `default_modes` unless you pass in a
    # specific set from the command line.
    generate_taint_models.run_generators(
        generators,
        default_modes=[
            "django_path_params"        ],
    )


if __name__ == "__main__":
    main()
