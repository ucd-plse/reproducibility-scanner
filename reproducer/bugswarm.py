import docker
import os, sys
import logging

from bugswarm.common.rest_api.database_api import DatabaseAPI

from utils import _run_command

docker_repo = 'bugswarm/images'
output_dir = 'outputs/bugswarm'

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class bugswarmReproducer(object):
    def __init__(self):
        pass

    @staticmethod
    def reproduce_buggy(bug_id):
        container = bugswarmReproducer.create_container(bug_id)
        container_id = container.short_id
        container.start()

        build_script_path = '/usr/local/bin/run_failed.sh'
        build_log_path = 'log-failed.log'
        travis_dir = '/home/travis'
        reproduce_cmd = 'bash -c \'bash {} > {}/{}\''.format(build_script_path, travis_dir, build_log_path)

        # run reproduce command in container
        _, stdout, stderr, ok = bugswarmReproducer.docker_exec_run(container_id, reproduce_cmd)
        # if not ok:
            # logging.error('Failed to run build command on buggy version')
            # logging.error(stderr)
            # logging.error(stdout)
        
        if not os.path.isdir('{}/reproduced/buggy'.format(output_dir)):
            _, stdout, stderr, ok = _run_command('mkdir -p {}/reproduced/buggy'.format(output_dir))
        
        log_file_src = '{}/{}'.format(travis_dir, build_log_path)
        log_file_dst = '{}/reproduced/buggy/{}.log'.format(output_dir, bug_id)

        # copy reproduced log
        _, stdout, stderr, ok = bugswarmReproducer.docker_cp(container_id, log_file_src, log_file_dst)
        if not ok:
            logging.error('Failed to copy log file from container to host')
            logging.error(stderr)
            logging.error(stdout)

        bugswarmReproducer.remove_container(container_id=container_id, force=True)

    @staticmethod
    def reproduce_fixed(bug_id):
        container = bugswarmReproducer.create_container(bug_id)
        container_id = container.short_id
        container.start()

        build_script_path = '/usr/local/bin/run_passed.sh'
        build_log_path = 'log-passed.log'
        travis_dir = '/home/travis'
        reproduce_cmd = 'bash -c \'bash {} > {}/{}\''.format(build_script_path, travis_dir, build_log_path)

        # run reproduce command in container
        _, stdout, stderr, ok = bugswarmReproducer.docker_exec_run(container_id, reproduce_cmd)
        # if not ok:
            # logging.error('Failed to run build command on fixed version')
            # logging.error(stderr)
            # logging.error(stdout)
        
        if not os.path.isdir('{}/reproduced/fixed'.format(output_dir)):
            _, stdout, stderr, ok = _run_command('mkdir -p {}/reproduced/fixed'.format(output_dir))
        
        log_file_src = '{}/{}'.format(travis_dir, build_log_path)
        log_file_dst = '{}/reproduced/fixed/{}.log'.format(output_dir, bug_id)

        # copy reproduced log
        _, stdout, stderr, ok = bugswarmReproducer.docker_cp(container_id, log_file_src, log_file_dst)
        if not ok:
            logging.error('Failed to copy log file from container to host')
            logging.error(stderr)
            logging.error(stdout)
        
        bugswarmReproducer.remove_container(container_id=container_id, force=True)

    @staticmethod
    def reproduce(bug_id):
        bugswarmReproducer.reproduce_buggy(bug_id)
        bugswarmReproducer.reproduce_fixed(bug_id)
        bugswarmReproducer.get_original_log(bug_id)


    @staticmethod
    def get_original_log(bug_id):
        
        # the bugswarm token was requested from http://www.bugswarm.org/contact/
        # we reveal the token here for replication purposes
        # please do not abuse this token
        bugswarm_token = 'pMWUOry6eJyj_OycTOXEDOW0MFmBSjFIIRjwWFBmzAc'
        bugswarm_api = DatabaseAPI(token=bugswarm_token)
        
        bug_info = bugswarm_api.find_artifact(bug_id).json()

        buggy_job_id = str(bug_info['failed_job']['job_id'])
        fixed_job_id = str(bug_info['passed_job']['job_id'])

        if not os.path.isdir('{}/original/buggy'.format(output_dir)):
            _, stdout, stderr, ok = _run_command('mkdir -p {}/original/buggy'.format(output_dir))
        if not os.path.isdir('{}/original/fixed'.format(output_dir)):
            _, stdout, stderr, ok = _run_command('mkdir -p {}/original/fixed'.format(output_dir))

        try:
            buggy_log = DatabaseAPI(token=bugswarm_token).get_build_log(buggy_job_id)
            fixed_log = DatabaseAPI(token=bugswarm_token).get_build_log(fixed_job_id)

            with open('{}/original/buggy/{}.log'.format(output_dir, bug_id), 'w') as f:
                f.write(buggy_log)
            
            with open('{}/original/fixed/{}.log'.format(output_dir, bug_id), 'w') as f:
                f.write(fixed_log)
        except Exception as e:
            logging.error('Failed to get original log')
            logging.error(e)


    @staticmethod
    def create_container(bug_id):
        _DOCKER_CLIENT = docker.from_env()
        docker_image_tag = '{}:{}'.format(docker_repo, bug_id)
        try:
            # do docker pull first to make sure the image is available
            image = _DOCKER_CLIENT.images.pull(docker_repo, tag=bug_id)
            # create container from image
            container = _DOCKER_CLIENT.containers.create(image=docker_image_tag, command='/bin/bash', tty=True)
        except docker.errors.APIError as err:
            logging.error('Failed to create Docker container for {} with: {}'.format(bug_id, err))
            sys.exit(1)
        return container

    @staticmethod
    def docker_exec_run(container_id, command):
        # default timeout is 20 mins per build
        return _run_command('timeout 20m docker exec {} {}'.format(container_id, command))

    @staticmethod
    def docker_cp(container_id, src, dst):
        return _run_command('docker cp {}:{} {}'.format(container_id, src, dst))
    
    @staticmethod
    def remove_container(container_id, force=False):
        if force:
            return _run_command('docker container rm {} -f'.format(container_id))
        else:
            return _run_command('docker container rm {}'.format(container_id))
