import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

export interface ErrorRecord {
  hash: string;
  message: string;
  scope: string;
  timestamp: string;
  context?: string;
  metadata?: Record<string, unknown>;
  location?: {
    file: string;
    line: number;
    className: string;
    funcName: string;
  };
}

export interface RegistryStatus {
  total: number;
  recent: ErrorRecord[];
}

export class Registry {
  private static instance: Registry;
  private readonly dir: string;
  private readonly filePath: string;

  private constructor() {
    this.dir = path.join(os.homedir(), '.amend');
    this.filePath = path.join(this.dir, 'errors.log');
    this.ensureDir();
  }

  static getInstance(): Registry {
    if (!Registry.instance) {
      Registry.instance = new Registry();
    }
    return Registry.instance;
  }

  private ensureDir(): void {
    if (!fs.existsSync(this.dir)) {
      fs.mkdirSync(this.dir, { recursive: true });
    }
  }

    record(error: {
    hash: string;
    message: string;
    scope: string;
    timestamp: string;
    context?: string;
    metadata?: Record<string, unknown>;
    location?: { file: string; line: number; className: string; funcName: string };
  }): void {
    const entry: ErrorRecord = {
      hash: error.hash,
      message: error.message,
      scope: error.scope,
      timestamp: error.timestamp,
      context: error.context,
      metadata: error.metadata,
      location: error.location,
    };
    const line = JSON.stringify(entry) + '\n';
    fs.appendFileSync(this.filePath, line, 'utf8');
  }

    getAll(): ErrorRecord[] {
    if (!fs.existsSync(this.filePath)) return [];
    const content = fs.readFileSync(this.filePath, 'utf8').trim();
    if (!content) return [];
    return content.split('\n').map((line) => JSON.parse(line) as ErrorRecord);
  }

    find(hash: string): ErrorRecord[] {
    return this.getAll().filter((r) => r.hash === hash || r.hash.startsWith(hash));
  }

    clear(): void {
    if (fs.existsSync(this.filePath)) {
      fs.writeFileSync(this.filePath, '', 'utf8');
    }
  }

    status(): RegistryStatus {
    const all = this.getAll();
    return {
      total: all.length,
      recent: all.slice(-5),
    };
  }

    exportTo(filePath: string, format: 'json' | 'log'): void {
    const all = this.getAll();
    let content: string;

    if (format === 'json') {
      content = JSON.stringify(all, null, 2);
    } else {
      const lines = all.map((r) => {
        const parts = [
          `[${r.timestamp}]`,
          `${r.hash}`,
          `${r.scope}: ${r.message}`,
        ];
        if (r.context) parts.push(`context: ${r.context}`);
        if (r.location) parts.push(`at ${r.location.file}:${r.location.line}`);
        return parts.join('  ');
      });
      content = lines.join('\n') + '\n';
    }

    const dir = path.dirname(filePath);
    if (dir && !fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(filePath, content, 'utf8');
  }

    getFilePath(): string {
    return this.filePath;
  }
}
