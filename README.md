# Getting Started

**THIS IS A TECHNICAL PREVIEW, MANY THINGS MAY NOT WORK CORRECTLY**

*We GLADLY ACCEPT PULL REQUESTS- GET CREDIT FOR YOUR WORK!*

```
$ docker pull csirtgadgets/verbose-robot
$ export CIF_TOKEN=`head -n 25000 /dev/urandom | openssl dgst -sha256`
$ docker run -e CIF_TOKEN="${CIF_TOKEN}" -it -d -p 5000:5000 --name verbose-robot csirtgadgets/verbose-robot
$ docker exec -it verbose-robot /bin/bash
$ cif -d -p
$ env | grep CIF_TOKEN
```

# Are you getting value from CIF?

[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=YZPQXDLNYZZ3W)

Did you learn something new? Something that would have taken you weeks or months to learn on your own?

# Design Goals

* Performance (Leaner, Faster).
* Cleaner, Concise APIs, Platform Driven
* Realtime Streaming and Correlation (PUB/SUB/WebSockets)
* Machine Learning Integration (SKLearn|TensorFlow)
* Statistical Probability/Confidence Model
* Native [CSIRTG-X](https://csirtg.io) Integration
* WebHooks Support (Slack)
* Graph Support (networkx)

# Getting Help
 * [the Wiki](https://github.com/csirtgadgets/verbose-robot/wiki)
 * [Known Issues](https://github.com/csirtgadgets/verbose-robot/issues?labels=bug&state=open)
 * [FAQ](https://github.com/csirtgadgets/verbose-robot/wiki/FAQ)

# Getting Involved
There are many ways to get involved with the project. If you have a new and exciting feature, or even a simple bugfix, simply [fork the repo](https://help.github.com/articles/fork-a-repo), create some simple test cases, [generate a pull-request](https://help.github.com/articles/using-pull-requests) and give yourself credit!

If you've never worked on a GitHub project, [this is a good piece](https://guides.github.com/activities/contributing-to-open-source) for getting started.

* [How To Contribute](contributing.md)  
* [Project Page](http://csirtgadgets.com/collective-intelligence-framework/)

# COPYRIGHT AND LICENSE

Copyright (C) 2018 [the CSIRT Gadgets](http://csirtgadgets.com)

Free use of this software is granted under the terms of the [Mozilla Public License (MPLv2)](https://www.mozilla.org/en-US/MPL/2.0/).
