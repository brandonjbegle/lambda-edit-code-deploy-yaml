import boto3
import botocore
import json
import os.path
import zipfile
import io
import shutil

def lambda_handler(event, context):
    # Declare the function to return all file paths of the particular directory
    def retrieve_file_paths(dirName):
        # setup file paths variable
        filePaths = []
        # Read all directory, subdirectories and file lists
        for root, dirs, files in os.walk(dirName):
            for file in files:
                filePaths.append(os.path.join(root, file))
        # return all paths
        return filePaths

    
    s3 = boto3.resource('s3')
    code_pipeline = boto3.client('codepipeline')
    
    BUCKET_NAME = event['CodePipeline.job']['data']['inputArtifacts'][0]['location']['s3Location']['bucketName']
    INPUT_KEY_ZIP = event['CodePipeline.job']['data']['inputArtifacts'][0]['location']['s3Location']['objectKey']
    OUTPUT_KEY_ZIP = event['CodePipeline.job']['data']['outputArtifacts'][0]['location']['s3Location']['objectKey']
    OUTPUT_KEY = OUTPUT_KEY_ZIP.split('/')[-1]
    TEMP_FILE_ZIP ='/tmp/input.zip'
    JOB_ID = event['CodePipeline.job']['id']
    ENV = event['CodePipeline.job']['data']['actionConfiguration']['configuration']['UserParameters']
    
    downloadedFile = s3.Bucket(BUCKET_NAME).download_file(INPUT_KEY_ZIP, TEMP_FILE_ZIP);
    
    zf = zipfile.ZipFile(TEMP_FILE_ZIP, 'r')
    zf.extractall('/tmp/output')
    zf.close()
    
    try:
        with open('/tmp/output/appspec.yml', 'r') as file:
            data = file.readlines()
            
            # ENV variables set in CodePipeline UserParameters
            # Modify the lines below as needed based for different lines and configurations
            
            if(ENV == 'production'):
                data[4] = '    destination: /var/www/html/\n'
            else:
                data[4] = '    destination: /var/www/html/\n'
            file.close
        
        with open('/tmp/output/appspec.yml', 'w') as file:
            file.writelines( data )
            file.close()
           
        # Additional changes I made for BeforeInstall and AfterInstall Scripts
        # Change directories and lines as necessary
            
        with open('/tmp/output/scripts/set_permissions.sh', 'r') as file:
            data = file.readlines()
            if(ENV == 'production'):
                data[1] = 'sudo chown -R ec2-user:apache /var/www/html/\n'
            else:
                data[1] = 'sudo chown -R ec2-user:apache /var/www/html/\n'
            file.close
        
        with open('/tmp/output/scripts/set_permissions.sh', 'w') as file:
            file.writelines( data )
            file.close()
            
        with open('/tmp/output/scripts/install_composer_dependencies.sh', 'r') as file:
            data = file.readlines()
            if(ENV == 'production'):
                data[1] = 'cd /var/www/html/\n'
                data[2] = 'chmod -R 774 /var/www/html/\n'
                data[4] = 'sudo chown -R apache:apache /var/www/html/\n'
            else:
                data[1] = 'cd /var/www/html/\n'
                data[2] = 'chmod -R 774 /var/www/html/\n'
                data[4] = 'sudo chown -R apache:apache /var/www/html/\n'
            file.close
        
        with open('/tmp/output/scripts/install_composer_dependencies.sh', 'w') as file:
            file.writelines( data )
            file.close()
    except Exception as e:
        code_pipeline.put_job_failure_result(JOB_ID, failureDetails={'message': message, 'type': 'JobFailed'})
        
    
    # Rezip all the files
    try:
        filePaths = retrieve_file_paths('/tmp/output')
        zip_file = zipfile.ZipFile('/tmp/' + OUTPUT_KEY, 'w', zipfile.ZIP_DEFLATED)
        with zip_file:
            # writing each file one by one
            for file in filePaths:
                fileLoc = file.replace('/tmp/output', '')
                zip_file.write(file, fileLoc)
        
        # Put files back to s3
        s3.meta.client.upload_file('/tmp/' + OUTPUT_KEY, BUCKET_NAME, OUTPUT_KEY_ZIP, ExtraArgs={"ServerSideEncryption": "aws:kms", 'SSEKMSKeyId':'alias/aws/s3'})
        code_pipeline.put_job_success_result(jobId=JOB_ID)
    except Exception as e:
        code_pipeline.put_job_failure_result(jobId=JOB_ID, failureDetails={'message':"failed", 'type': 'JobFailed'})
    print(event)
    
    return 'Complete'