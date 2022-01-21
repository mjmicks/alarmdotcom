# Alarm.com Custom Component for [Home Assistant](https://www.home-assistant.io/)

## Intro

This is a custom component to allow Home Assistant to interface with the [Alarm.com](https://www.alarm.com/) site by scraping the Alarm.com web portal. This component is designed to integrate the Alarm.com security system functionality only - it requires an Alarm.com package which includes security system support.

Please note that Alarm.com may remove access at any time.

## Safety Warnings

This integration is great for casual use within Home Assistant but... **do not rely on this integration to keep you safe.**

1. This integration communicates with Alarm.com over an unofficial channel that can be broken or shut down at any time.
2. It may take several minutes for this device to receive a status update from Alarm.com's servers.
3. Your automations may be buggy.
4. This code may be buggy.

## Supported Devices

| Device Type  | Actions                               | View Status | Low Battery Sub-Sensor | Malfunction Sub-Sensor |
| ------------ | ------------------------------------- | ----------- | ---------------------- | ---------------------- |
| Alarm System | arm away, arm stay, arm night, disarm | ✔           |                        | ✔                      |
| Sensors      | _(none)_                              | ✔           | ✔                      | ✔                      |
| Locks        | lock, unlock                          | ✔           | ✔                      | ✔                      |
| Garage Door  | open, close                           | ✔           |                        |                        |

As of v0.2.0, multiples of all of the above devices are supported.

## Supported Sensors

1. Contact Sensor
2. Smoke Detector
3. CO Detector
4. Panic Button
5. Glass Break Detector

## Installation

1. Use [HACS](https://hacs.xyz/) to download this integration.
2. Configure the integration via Home Assistant's Integrations page. (Configuration -> Add Integration -> Alarm.com)
3. When prompted, enter your Alarm.com username, password, and two-factor authentication cookie (more info on this below).

## Configuration

You'll be prompted to enter these parameters when configuring the integration.

| Parameter         | Required | Description                                                                   |
| ----------------- | -------- | ----------------------------------------------------------------------------- |
| Username          | Yes      | Username for your Alarm.com account.                                          |
| Password          | Yes      | Password for your Alarm.com account.                                          |
| Two Factor Cookie | Maybe    | Required for accounts with two-factor authentication enabled. See note below. |

### Two Factor Authentication Cookie

Some providers are starting to require 2FA for logins. This can be worked around by getting the `twoFactorAuthenticationId` cookie from an already authenticated browser and entering it as a configuration parameter.

<details>
  <summary><b>Getting a Two Factor Authentication Cookie</b></summary>
    1. Temporarily remove your alarmdotcom config from configuration.yaml. (If the component is enabled it will keep trying to log in which will disrupt your initial 2FA setup)
    2. Log in to your account on the Alarm.com website: https://www.alarm.com/login.aspx
    3. Enable Two Factor Authentication
    4. Once you are fully logged in to the alarm.com portal without any more 2FA nag screens, go into the developer tools in your browser and locate the `twoFactorAuthenticationId` cookie. Instructions for locating the cookie in Chrome can be found here: https://developers.google.com/web/tools/chrome-devtools/storage/cookies
    5. Copy the cookie string into your config under the `Two Factor Cookie` parameter.
</details>

### Additional Options

These options can be set using the "Configure" button on the Alarm.com card on Home Assistant's Integrations page.

| Parameter      | Description                                                                                         |
| -------------- | --------------------------------------------------------------------------------------------------- |
| Code           | Specifies a code to arm/disarm your alarm or lock/unlock your locks in the Home Assistant frontend. |
| Force Bypass   | Specifies when to use the "force bypass" setting when arming.                                       |
| No Entry Delay | Specifies when to use the "no entry delay" setting when arming.                                     |
| Silent Arming  | Specifies when to use the "silent arming" setting when arming.                                      |

_The three arming options are not available on all systems/providers. Also, some combinations of these options are incompatible. If arming does not work with a combination of options, please check that you are able to arm via the web portal using those same options._
