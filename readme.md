## What is it?

The `ml-interface` repository is intended to eventually be a standalone library that games can use to interface with various text-generation endpoints in one "easy" to use library.

Currently, it's very hardcoded for my current project: [Something Else](https://www.danieltperry.me/project/2023-something-else/) (a mod for OpenMW), as it's still very early stages.

## Usage
> **Note**: Detailed instructions for installing Something Else / OpenMW can be found in the doc directory, or by [clicking here](doc/openmw-install.md).

Generically, the repository can be used as follows...

> **Warning**: The following may be out of date, things are still in very early development. Check the scripts for the most accurate information.

### Installation
* Run `ml-interface.sh init` to create the venv and install dependencies.
  * This creates a virtualenv called 'openmw_ml' in `~/.venv/openmw_ml` with a few dependencies installed.
  * To delete the venv, run `ml-interface.sh clean`.

### Running
* Create an input json for the model you wish to run.
  * The schema/layout of the json depends on the model being run, so there is no generic example available.
  * For model-specific examples, look inside the `input` folder of the model you wish to run.
* ~~Set environment variable `VENV_NAME` to the name of the conda environment you created above.~~
  * **TODO**: Not yet impletmented, currently the script is hardcoded to run scripts in the `openmw_ml` environment.
* Execute `ml-interface.sh`.
  * Example: `ml-interface.sh openai_chat /path/to/input.json`