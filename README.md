Unity3D Android notification plugin
=====
License: *MIT*

Gaben will connect to your Slack and wait for DM (could be invited to a channel aswell) to pull your last changes from git and start to build your project. On finish he will send your build back to Slack (if it's big you can grab it locally).
It's supposed to set up on separate PC to make a building process simplier when you have many developers.

Requirements listed in the file requirements.txt
Also it has embeded python Slack client (it has few fixes, so a can not use a package) from https://github.com/slackapi/python-slackclient

### Config

Please fill next properties in config.py before use:
* API_KEY - Slack api key (https://sgnew.slack.com/apps/manage/custom-integrations). More info here: https://github.com/slackapi/python-slackclient
* DONT_PRINT_USAGE_FOR - channel identificators. If you're gonna invite Gaben to channel fill this list with those channels to resctirct him print commang usage there (channel ID you can get from slack url in the web version, when channel is selected)
* REP_DIRECTORY - empty directory to keep your repositories, build and logs
* UNITY - your Unity installations, key is a version, value is a path to Unity editor

### Projects

Your settings are contained in projects.yml file. Every project has parameters:
* name - name of the project. Generally generated from git url.
* url - url of the git repository
* unity - version of Unity to use
* keystore_filename - your keystore path relative to root project directory
* keystore_pwd - password for keystore
* key - key name for the keystore
* key_pwd - password for the key

In general you shouldn't edit this file manually, you can use bot commands for that.

### Usage

Just run ./gaben.py (you can invite him to a channel) and say **help** to get commands and usage