## Analytics MANUAL Deployment


#### Step 1:  Go to the release url and download the ZIP file

```
https://github.com/PrescriptiveData/datascience/archive/v0.4.zip
```


#### Step 2: Unzip the file and upload to S3

```
$ aws s3 sync TPO2-Rudin s3://pdanalytics/v0.4-8aebb42
```

#### Step 3: Open the Vagrantfile and look for the following information

```
aws.instance_type = "r3.large"
aws.ami = "ami-d05e75b8"
```

#### Step 4: Go to EC2 Console and Spin a new instance based on the 
parameters obtained before

The instance should have an IAM role that allows reads to an S3 Bucket

#### Step5: Log into the machine
```
$ssh ubuntu@[public_dns]
```

#### Step 6: Install dependencies

```
$ sudo apt-get install awscli
$ sudo apt-get install python-pip
$ sudo apt-get install unzip
```

Download and Install the Python 2.7 version of  Anaconda 2.4.1 (64-bit)]

Go to https://www.continuum.io/downloads#_unix and copy the download link

Download in the /tmp directory
```
$ cd /tmp
$ wget [Link_copied from continuum.io for Linux 64-bit]
```

After downloading the installer, in your terminal window execute
```
$ bash Anaconda2-2.4.1-Linux-x86_64.sh
```

#### Step 7: Install Larkin source code

Create directory
```
$ mkdir /var/larkin
$ cd /var/larkin
```

Download from S3
```
$ aws s3 sync s3://pdanalytics/v0.4-8aebb42 ./
```

Install python dependencies
```
$ pip install requirements.txt
```
