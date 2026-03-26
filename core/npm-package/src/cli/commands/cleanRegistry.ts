import { Command } from 'commander';
import { Registry } from '../../registry/Registry.js';
import * as readline from 'readline';

export function cleanRegistryCommand(program: Command): void {
  program
    .command('clean')
    .argument('[target]', 'What to clean (registry)', 'registry')
    .description('Clear all registered errors from the registry')
    .action(async (target: string) => {
      if (target !== 'registry') {
        console.log(`Unknown target: ${target}. Did you mean "amend clean registry"?`);
        return;
      }

      const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
      });

      const answer = await new Promise<string>((resolve) => {
        rl.question('Are you sure you want to clear the entire registry? [y/N] ', resolve);
      });
      rl.close();

      if (answer.toLowerCase() === 'y' || answer.toLowerCase() === 'yes') {
        Registry.getInstance().clear();
        console.log('Registry cleared.');
      } else {
        console.log('Aborted.');
      }
    });
}
