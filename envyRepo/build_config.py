import configparser

if __name__ == '__main__':
    default_data = {
        'ENVYPATH': 'Z:/ENVY/',
    }
    with open('config.ini', 'w') as config_file:
        config = configparser.ConfigParser()
        config['DEFAULT'] = default_data
        config.write(config_file)