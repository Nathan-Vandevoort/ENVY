import configparser

if __name__ == '__main__':
    default_data = {
        'DISCOVERYPORT': 37020,
        'ENVYPATH': 'Z:/ENVY/',
        'REPOPATH': '//titansrv/studentShare/__ENVY__/ENVY_Repo/',
        'HOUDINIBINPATH': 'C:/Program Files/Side Effects Software/Houdini 20.0.653/bin/',
        'TEMP': 'C:/Temp/',
    }
    with open('config.ini', 'w') as config_file:
        config = configparser.ConfigParser()
        config['DEFAULT'] = default_data
        config.write(config_file)