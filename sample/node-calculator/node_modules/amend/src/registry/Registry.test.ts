import { expect, test, describe, beforeAll, afterAll, beforeEach } from 'vitest';
import { Registry } from './Registry.js';
import { encode } from './CoreEngine.js';
import { logger } from '../tests/logger.js';
import * as path from 'path';
import * as os from 'os';
import * as fs from 'fs';

describe('Registry Functionality', () => {
  let registry: Registry;
  let testKey1: string;
  let testKey2: string;

  beforeAll(() => {
    logger.info('Registry', 'Starting Registry test suite');
    registry = Registry.getInstance();
    
    testKey1 = encode('src/test.ts', 10, 'TestClass', 'testMethod', 'First Error', 'ScopeError');
    testKey2 = encode('src/other.ts', 20, '', 'otherMethod', 'Second Error', 'NetworkError');
  });

  beforeEach(() => {
    registry.clear();
  });

  afterAll(() => {
    registry.clear();
    logger.success('Registry', 'Finished Registry test suite');
  });

  test('Records single entry accurately', () => {
    logger.info('Registry', 'Test: Record single entry');
    registry.record({
      key: testKey1,
      timestamp: new Date().toISOString()
    });

    const all = registry.getAll();
    expect(all.length).toBe(1);
    expect(all[0].key).toBe(testKey1);
    expect(all[0].count).toBe(1);
    logger.info('Registry', `Successfully recorded and retrieved 1 entry.`);
  });

  test('Aggregates multiple identical errors', () => {
    logger.info('Registry', 'Test: Occurrences aggregation');
    
    registry.record({ key: testKey1, timestamp: new Date().toISOString() });
    registry.record({ key: testKey1, timestamp: new Date().toISOString() });
    registry.record({ key: testKey1, timestamp: new Date().toISOString() });
    
    registry.record({ key: testKey2, timestamp: new Date().toISOString() });

    const all = registry.getAll();
    logger.info('Registry', `Retrieved ${all.length} unique aggregated records.`);
    
    expect(all.length).toBe(2);
    
    const record1 = all.find(r => r.key === testKey1);
    expect(record1?.count).toBe(3);
    
    const record2 = all.find(r => r.key === testKey2);
    expect(record2?.count).toBe(1);
  });

  test('Exports correctly to log format', () => {
    logger.info('Registry', 'Test: Export functionality');
    registry.record({ key: testKey1, timestamp: new Date().toISOString() });
    
    const exportPath = path.join(os.homedir(), '.amend', 'test-export.log');
    registry.exportTo(exportPath, 'log');
    
    const exists = fs.existsSync(exportPath);
    logger.info('Registry', `Export file created: ${exists}`);
    expect(exists).toBe(true);
    
    const content = fs.readFileSync(exportPath, 'utf8');
    expect(content).toContain(testKey1);
    expect(content).toContain('ScopeError');
    
    fs.unlinkSync(exportPath);
  });
});
