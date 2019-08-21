# Edit Appspec.yaml Lambda Function For AWS CodePipeline

Simple python script that allows for changing the AppSpec.yaml on the fly in case of different configurations for production and development.

## How does it work?

- Copy this code to a lambda function in your AWS account
- Modify the line that says ‘    destination: XXXXXX’ to match where your code needs to deploy to.
- Modify the index of the array to match your AppSpec.yaml line. Mine was line 5, thus data[4].
- Make modifications/remove the script editing portions of the file. This function modifies some shell scripts that were in the application folder based on production/development.
- Make sure your lambda function has a role that gives it access to the S3 bucket where your input artifact will be stored and CodePipelines so it can update the status to failure or success.
