
const isProduction = process.env.NODE_ENV === 'production';

const getTimestamp = () => {
    return new Date().toISOString().replace('T', ' ').split('.')[0];
};

const formatMessage = (level, message, component) => {
    const timestamp = getTimestamp();
    
    const prefix = component ? `[${timestamp}] [${level}] [${component}]` : `[${timestamp}] [${level}]`;
    return `${prefix} - ${message}`;
};

const logger = {
    info: (message, component = '') => {
        console.log(`%c${formatMessage('INFO', message, component)}`, 'color: #2ecc71; font-weight: bold;');
    },

    error: (message, component = '') => {
        console.error(`%c${formatMessage('ERROR', message, component)}`, 'color: #e74c3c; font-weight: bold;');
    },

    warn: (message, component = '') => {
        console.warn(`%c${formatMessage('WARN', message, component)}`, 'color: #f39c12; font-weight: bold;');
    },

    debug: (message, component = '') => {
        
        if (!isProduction) {
            console.log(`%c${formatMessage('DEBUG', message, component)}`, 'color: gray;');
        }
    }
};

export default logger;