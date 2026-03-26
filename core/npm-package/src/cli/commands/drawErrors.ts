import { Command } from 'commander';
import { Registry } from '../../registry/Registry.js';

export function drawErrorsCommand(program: Command): void {
  program
    .command('drawErrors')
    .description('List all registered errors (hash + message)')
    .action(() => {
      const records = Registry.getInstance().getAll();

      if (records.length === 0) {
        console.log('No errors registered.');
        return;
      }

      const hashWidth = 20;
      console.log(
        'HASH'.padEnd(hashWidth) + 'MESSAGE'
      );

      for (const r of records) {
        console.log(
          r.hash.padEnd(hashWidth) + r.message
        );
      }
    });
}
