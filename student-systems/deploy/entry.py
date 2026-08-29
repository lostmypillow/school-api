#!/usr/bin/env python3
import os  # noqa: EXE001

import aws_cdk as cdk

from deploy.stack import SearchStack

app = cdk.App()
SearchStack(
    app,
    "SearchStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

app.synth()
