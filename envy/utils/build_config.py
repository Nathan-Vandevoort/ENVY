import configparser

if __name__ == '__main__':
    default_data = {
        'DISCOVERYPORT': 37020,
        'ENVYPATH': 'Z:/ENVY/',
        'REPOPATH': '//titansrv/studentShare/__ENVY__/ENVY_Repo/',
        'HOUDINIBINPATH': 'C:/Program Files/Side Effects Software/Houdini 20.0.653/bin/',
        'MAYABINPATH': 'C:/Program Files/Autodesk/Maya2024/bin',
        'TEMP': 'C:/Temp/',
        'COMPUTERPREFIXES': ['LAB1-', 'LAB2-', 'LAB3-', 'LAB4-', 'LAB5-', 'LAB6-', 'LAB7-', 'LAB8-', 'LAB9-', 'LEC1', 'LEC2', 'LEC3', 'VR1']
    }

    with open('../config.ini', 'w') as config_file:
        config = configparser.ConfigParser()
        config['DEFAULT'] = default_data
        config.write(config_file)
