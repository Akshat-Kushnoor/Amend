import { expect, test, describe, beforeAll, afterAll } from 'vitest';
import { AgentConfig } from './AgentConfig.js';
import { logger } from '../tests/logger.js';

describe('AgentConfig Functionality', () => {
  let config: AgentConfig;

  beforeAll(() => {
    logger.info('AgentConfig', 'Starting AgentConfig test suite');
    config = AgentConfig.getInstance();
  });

  afterAll(() => {
    logger.success('AgentConfig', 'Finished AgentConfig test suite');
  });

  test('Manages hints map correctly', () => {
    logger.info('AgentConfig', 'Test: Hints mapping');
    config.setHint('hash123', 'Check the database connection');
    
    const hint = config.getHint('hash123');
    logger.info('AgentConfig', `Retrieved hint: ${hint}`);
    expect(hint).toBe('Check the database connection');
    
    config.clearHint('hash123');
    expect(config.getHint('hash123')).toBeUndefined();
  });

  test('Handles path scoping', () => {
    logger.info('AgentConfig', 'Test: Path scoping');
    
    expect(config.isEnabled('src/some/file.ts')).toBe(true);

    config.disable('src/secret');
    expect(config.isEnabled('src/secret/keys.ts')).toBe(false);
    expect(config.isEnabled('src/public/index.ts')).toBe(true);

    logger.info('AgentConfig', `Secret path enabled status: ${config.isEnabled('src/secret/keys.ts')}`);

    config.enable('src/restricted');
    expect(config.isEnabled('src/restricted/area.ts')).toBe(true);
    expect(config.isEnabled('src/public/index.ts')).toBe(false);
    
    // reset for next tests if any
    config.disable('src/restricted');
    config.enable('src/public');
  });
});
