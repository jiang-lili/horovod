# Copyright 2020 Uber Technologies, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

from __future__ import print_function

import six
import sys
import traceback

from horovod.run.common.util import safe_shell_exec


def execute(command):
    """
    Executes the command and returns stdout and stderr as a string, together with the exit code.
    :param command: command to execute
    :return: (output, exit code) or None on failure
    """
    output = six.StringIO()
    try:
        exit_code = safe_shell_exec.execute(command, stdout=output, stderr=output)
        output_msg = output.getvalue()
    except Exception:
        print(traceback.format_exc(), file=sys.stderr)
        return None
    finally:
        output.close()

    return output_msg, exit_code
