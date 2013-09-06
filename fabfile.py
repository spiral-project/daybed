from fabric.api import env, cd, sudo

env.hosts = ['172.19.2.112']


def deploy_server():
    with cd('/home/www/daybed.lolnet.org/daybed'):
        sudo('git pull', user="www-data")
        sudo('bin/python setup.py develop', user="www-data")
    sudo('supervisorctl restart daybed.lolnet.org')


def deploy_ui():
    with cd('/home/www/daybed.lolnet.org/daybed-ui'):
        sudo('git pull', user="www-data")


def deploy():
    deploy_ui()
    deploy_server()
