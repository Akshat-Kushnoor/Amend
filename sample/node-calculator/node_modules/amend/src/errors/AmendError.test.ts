import { expect, test, describe, beforeAll, afterAll } from 'vitest';
import { AmendError } from './AmendError.js';
import { Registry } from '../registry/Registry.js';
import { logger } from '../tests/logger.js';
import { decode } from '../registry/CoreEngine.js';

describe('AmendError Functionality', () => {
  beforeAll(() => {
    logger.info('AmendError', 'Starting AmendError test suite');
    Registry.getInstance().clear();
  });

  afterAll(() => {
    logger.success('AmendError', 'Finished AmendError test suite');
  });

  test('Creates error with correct class and message', () => {
    logger.info('AmendError', 'Test: Should initialize basic error');
    
    const err = new AmendError('Something broke', 'ScopeError');
    expect(err.message).toBe('Something broke');
    expect(err.name).toBe('ScopeError');
    expect(err.key).toBeDefined();
    
    logger.info('AmendError', `Generated key: ${err.key}`);
    expect(err.key.startsWith('amend:SCO.')).toBe(true);
  });

  test('Extracts correct filepath from stack', () => {
    logger.info('AmendError', 'Test: Stack trace extraction for location');
    
    const throwIt = () => {
        return new AmendError('Network down', 'NetworkError');
    };

    const err = throwIt();
    logger.info('AmendError', `Extracted key: ${err.key}`);

    const decoded = decode(err.key);
    
    logger.info('AmendError', `Decoded filepath: ${decoded.filePath}`);
    expect(decoded.filePath.replace(/\\/g, '/')).toContain('src/errors/AmendError.test.ts');
  });

  test('Writes to Registry on creation', () => {
    logger.info('AmendError', 'Test: Auto-registry functionality');
    const registry = Registry.getInstance();
    const initialCount = registry.getAll().length;
    
    new AmendError('Test registry', 'ValidationError');
    
    const newCount = registry.getAll().length;
    logger.info('AmendError', `Registry record count went from ${initialCount} to ${newCount}`);
    expect(newCount).toBeGreaterThan(initialCount);
  });
});
