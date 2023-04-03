# Installation

<!-- Hi there, this isn't really ready for general usage yet since it's so hacked together, but if you're reading this, maybe you want to give it a shot anyway? -->
Since the mod is in such an early state, there's currently no easy way to try this mod out. There's no binary distribution available.

However, if you're desperate, you can build it yourself from source. There's currently two ways to do it (but, practically, it's really just one way). You need to have some amount of development experience to be able to figure it out, though.

Neither way is guaranteed to work, since things are still in early development. I do try to make sure things are working when I push them, but I can't guarantee they will work for you when you try it.

The mod is currently only tested on Mac, with Linux support assumed. Windows currently is not supported at all.

> **Note**: Windows support wouldn't be too hard to add (most of the heavy lifting is done by Python and Conda), but there's some `.sh` scripts that are run as part of the text-generation process that would have to be replaced with batch scripts.

## Prerequisites
Regardless of which option you go with, you need to set up the ML environment first. While running the game,  [miniconda](https://docs.conda.io/en/latest/miniconda.html) (or similar) must be available for the game to run. The game uses `conda run` to run the models.

Set up a new environment called `openmw_ml` and install the the following packages:
* `python=3.11`
* `transformers`
* `sentencepiece`
* `openai`

This environment will be used by the mod to generate text. Once your environment is set up, continue onto either option 1 or 2 below.

## Option 1 - Nix (Easiest)
Nix itself isn't the easiest thing to use, but I have commands for you to use below that should work for anybody, if you can get Nix installed.

If you already have a clone of nixpkgs available locally, add my [GitHub fork](https://github.com/Netruk44/nixpkgs): `https://github.com/Netruk44/nixpkgs`, and checkout the branch `openmw-ipc-mod`, then build the package `openmw-mod-something-else`.

For example:
```bash
cd /path/to/your/nixpkgs

# Or clone it if you don't have it already:
# git clone https://github.com/NixOS/nixpkgs.git

git remote add netruk44 https://github.com/Netruk44/nixpkgs
git fetch netruk44
git checkout -b openmw-ipc-mod netruk44/openmw-ipc-mod
nix-build . -A openmw-mod-something-else
```

If you don't have a clone of nixpkgs, and don't want to bother, you can use the following command to just build it without making a clone of nixpkgs:

> **Note**: Be warned that it will take a few minutes to download the entire repository archive. And you'll have to redownload the entire thing every time I push an update.
> 
> It would probably be worth your time to instead use git and clone nixpkgs if you ever decide to rebuild the mod.

**With flakes enabled**:
```bash
nix build "git+https://github.com/Netruk44/nixpkgs?ref=openmw-ipc-mod"#openmw-mod-something-else
```

**Without flakes enabled**:
```bash
nix-build "https://github.com/Netruk44/nixpkgs/archive/openmw-ipc-mod.tar.gz" -A openmw-mod-something-else
```

Once the command is complete, you should have a usable build of the game in the `result` folder. You can run it by running the `openmw` binary in the `bin` folder on Linux, or by using `open result/OpenMW.App` on Mac.

## Option 2 - Make it yourself
Practically infeasible for most people, but if you're an experienced developer, you can try to build it yourself. Requires knowledge of how to build OpenMW, I'm not going to be explaining that piece 😊.

> Nix automates all of this for you, which is why it's the recommended way to build this mod.

First get your build of OpenMW running. Follow [their instructions for that](https://wiki.openmw.org/index.php?title=Development_Environment_Setup).

Then setup the following repositories...

* ml-interface:
  * The part of the mod that handles the text generation by either running a local model or by calling an API.
  * Clone from my github: `https://github.com/Netruk44/ml-interface.git`
  * Mark down the path where you cloned it to, you'll need it later (`$ML_INTERFACE_PATH`)
* OpenMW:
  * Add my fork as a remote: `https://gitlab.com/Netruk44/openmw.git`
  * Checkout the branch: `something-else-mod`
  * Build it: `make`
  * Create a shell script in the output binary folder next to `openmw` called `custom_answer` with just one line:
    * `$ML_INTERFACE_PATH/ml-interface.sh "$@"`

After that, you should be able to see and use the new `Something Else...` button in the dialogue menu.