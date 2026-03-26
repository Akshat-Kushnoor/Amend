import { amendHash } from '../registry/hash.js';
import { Registry } from '../registry/Registry.js';

export interface AmendErrorOptions {
  context?: string;
  metadata?: Record<string, unknown>;
}

export class AmendError extends Error {
  readonly hash: string;
  readonly scope: string;
  readonly timestamp: string;
  readonly context?: string;
  readonly metadata?: Record<string, unknown>;
  readonly location: {
    file: string;
    line: number;
    className: string;
    funcName: string;
  };

  constructor(message: string, errorClass: string, options?: AmendErrorOptions) {
    super(message);
    this.name = errorClass;
    this.scope = this.constructor.name;
    this.timestamp = new Date().toISOString();

    const frames = this.stack?.split('\n') ?? [];
    let filePath = 'unknown';
    let line = 0;
    let className = '';
    let funcName = 'unknown';

    for (let i = 2; i < frames.length; i++) {
      const frame = frames[i];
      if (frame.includes('node_modules/amend') || frame.includes('AmendError')) continue;

      const match = frame.match(/at (?:(.+?)\.)?(.+?) \((.+?):(\d+):\d+\)/);
      if (match) {
        className = match[1] ?? '';
        funcName  = match[2];
        filePath  = match[3].replace(process.cwd() + '/', '').replace(process.cwd() + '\\', '');
        line      = parseInt(match[4]);
        break;
      }

      const simpleMatch = frame.match(/at (.+?):(\d+):\d+/);
      if (simpleMatch) {
        filePath = simpleMatch[1].replace(process.cwd() + '/', '').replace(process.cwd() + '\\', '');
        line     = parseInt(simpleMatch[2]);
        break;
      }
    }

    this.location = { file: filePath, line, className, funcName };

    this.hash = amendHash(filePath, line, className, funcName, message, errorClass);

    this.context  = options?.context;
    this.metadata = options?.metadata;

    Registry.getInstance().record(this);
  }
}
