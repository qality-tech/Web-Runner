# WebRunner
The purpose of this project is to listen to a rabbitmq queue and start a run tests independently, one test at a time.

# Moto:
The test logs should be stored locally and be sent to the [RunnerManager](https://github.com/qality-tech/Runner-Manager) as many times as needed via the local rabbitmq. They are critical for the test's lifetime.

- The runners should be split on technology. This is the Web and API one.
- Multiple runners of the same technology can be started simultaneously. Where applicable and makes sense they can be started in docker containers.

The reports can significantly vary in size, complexity and intensity thus an API approach is not suitable.
For each test running in a runner a new temporary queue is created and the shovel plugin is used to relay the messages to the main rabbitmq instance.
Each runner such as this one pushes the logs to the local rabbitmq instance and the [RunnerManager](https://github.com/qality-tech/Runner-Manager) manages the rest.

# Installation:
- Install Python 3.10+
- Install pipenv 2024.0.1 or any other virtual environment manager
- Run `python pipenv install` to install the dependencies or the equivalent command for your virtual environment manager
- Copy `config.env.example` to `config.env` and fill in the necessary values
- Run `python RunnerManager.py` to start the runner manager
- Use the [QAlity website](http://wu.qality.tech/) to start tests on the runner manager with your name 
- Enjoy
