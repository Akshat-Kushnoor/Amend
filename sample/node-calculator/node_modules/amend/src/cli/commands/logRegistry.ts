import { Command } from 'commander';
import { Registry } from '../../registry/Registry.js';

export function logRegistryCommand(program: Command): void {
  program
    .command('logRegistry <filepath>')
    .description('Export all registered errors to a file (.json or .log)')
    .action((filepath: string) => {
      const cleanPath = filepath.replace(/^--/, '');

      let format: 'json' | 'log';
      if (cleanPath.endsWith('.json')) {
        format = 'json';
      } else if (cleanPath.endsWith('.log')) {
        format = 'log';
      } else {
        console.log('Unsupported file extension. Use .json or .log');
        return;
      }

      Registry.getInstance().exportTo(cleanPath, format);
      console.log(`Registry exported to ${cleanPath} (${format} format)`);
    });
}
