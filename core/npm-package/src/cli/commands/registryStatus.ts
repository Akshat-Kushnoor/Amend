import { Command } from 'commander';
import { Registry } from '../../registry/Registry.js';

export function registryStatusCommand(program: Command): void {
  program
    .command('registry')
    .argument('[action]', 'Action to perform (status)', 'status')
    .description('Show registry status, totals, and recent errors')
    .action((action: string) => {
      if (action !== 'status') {
        console.log(`Unknown action: ${action}. Did you mean "amend registry status"?`);
        return;
      }

      const { total, recent } = Registry.getInstance().status();

      console.log('[amend registry status]\n');
      console.log(`  Total errors    : ${total}`);
      console.log(`  Recent errors   : ${recent.length}\n`);

      if (recent.length > 0) {
        const hashW = 20;
        const msgW  = 25;
        console.log(
          '  ' + 'HASH'.padEnd(hashW) + 'MESSAGE'.padEnd(msgW) + 'FILE'
        );

        for (const r of recent) {
          const file = r.location?.file ?? '(unknown)';
          console.log(
            '  ' + r.hash.padEnd(hashW) + r.message.padEnd(msgW) + file
          );
        }
      }

      if (total > 0) {
        const all = Registry.getInstance().getAll();

        const scopeCount: Record<string, number> = {};
        for (const r of all) {
          scopeCount[r.scope] = (scopeCount[r.scope] ?? 0) + 1;
        }
        const topScope = Object.entries(scopeCount).sort((a, b) => b[1] - a[1])[0];

        const now = Date.now();
        const last24h = all.filter((r) => now - new Date(r.timestamp).getTime() < 86_400_000).length;

        console.log('\n  Analytics:');
        if (topScope) {
          console.log(`    Most common scope : ${topScope[0]}`);
        }
        console.log(`    Last 24h          : ${last24h} errors`);
      }
    });
}
