
# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Deployment Requirements

### Docker
This project requires [Docker](https://www.docker.com/products/docker-desktop/) to be installed and running on your machine. Docker is used by AWS CDK to bundle Lambda layers and functions in a Linux environment, which matches the AWS Lambda runtime. If Docker is not running, deployment will fail with an error like `spawnSync docker ENOENT`.

**Install Docker Desktop:**
- [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Install and start Docker before running `cdk deploy`.

### Python Dependencies for Lambda (web3)
The AWS Lambda environment is Linux-based. To ensure compatibility, the `web3` library (and its dependencies) must be installed into a Lambda layer using a Linux environment. The deployment process uses Docker to do this automatically, so the resulting layer works correctly on AWS Lambda.

**Why is this needed?**
- If you install `web3` on Windows or Mac and upload it directly, it may not work on AWS Lambda due to binary incompatibilities.
- Docker ensures the dependencies are built for the correct platform.

**Summary:**
- Make sure Docker is running before deploying.
- The deployment process will automatically bundle `web3` in a Lambda layer using Docker for AWS compatibility.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
