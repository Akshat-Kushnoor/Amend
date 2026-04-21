import * as fs from 'fs';
import * as path from 'path';

class TestLogger {
  private logFile: string;

  constructor() {
    this.logFile = path.join(process.cwd(), 'test-execution.log');
    // Clear out the previous run
    if (fs.existsSync(this.logFile)) {
      fs.writeFileSync(this.logFile, '', 'utf8');
    }
  }

  private write(level: string, context: string, message: string) {
    const time = new Date().toISOString();
    const formatted = `[${time}] [${level}] [${context}] ${message}`;
    
    // Output to console with basic terminal colors
    if (level === 'ERROR') {
      console.error(`\x1b[31m${formatted}\x1b[0m`);
    } else if (level === 'WARN') {
      console.warn(`\x1b[33m${formatted}\x1b[0m`);
    } else if (level === 'SUCCESS') {
      console.log(`\x1b[32m${formatted}\x1b[0m`);
    } else {
      console.log(`\x1b[36m${formatted}\x1b[0m`); // cyan for INFO
    }

    // Append to file
    fs.appendFileSync(this.logFile, formatted + '\n', 'utf8');
  }

  info(context: string, message: string) {
    this.write('INFO', context, message);
  }

  warn(context: string, message: string) {
    this.write('WARN', context, message);
  }

  error(context: string, message: string) {
    this.write('ERROR', context, message);
  }

  success(context: string, message: string) {
    this.write('SUCCESS', context, message);
  }
}

export const logger = new TestLogger();
