import { Command } from 'commander';
import { Registry } from '../../registry/Registry.js';

export function pinCommand(program: Command): void {
  program
    .command('pin <hash>')
    .description('Show full details for an error by its hash')
    .action((hash: string) => {
      const cleanHash = hash.replace(/^--/, '');

      const matches = Registry.getInstance().find(cleanHash);

      if (matches.length === 0) {
        console.log(`No error found for hash: ${cleanHash}`);
        return;
      }

      const r = matches[matches.length - 1];

      console.log(`[amend pin ${r.hash}]\n`);
      console.log(`  Message   : ${r.message}`);
      console.log(`  Timestamp : ${r.timestamp}`);
      console.log(`  Context   : ${r.context ?? '(none)'}`);
      console.log(`  Metadata  : ${r.metadata ? JSON.stringify(r.metadata) : '(none)'}`);

      if (matches.length > 1) {
        console.log(`\n  seen      : ${matches.length} times  ·  last ${r.timestamp}`);
      }
    });
}
