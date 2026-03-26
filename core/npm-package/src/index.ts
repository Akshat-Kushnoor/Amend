import { ScopeError } from './errors/scopeError.js';
import { NetworkError } from './errors/networkError.js';
import { ValidationError } from './errors/validationError.js';
import { Registry } from './registry/Registry.js';
import { AgentConfig } from './ai/AgentConfig.js';

const registry = Registry.getInstance();
const ai = AgentConfig.getInstance();

const amend = {
  ScopeError,
  NetworkError,
  ValidationError,

  registry: {
    getAll:    ()                                          => registry.getAll(),
    find:      (hash: string)                             => registry.find(hash),
    clear:     ()                                         => registry.clear(),
    status:    ()                                         => registry.status(),
    exportTo:  (filePath: string, format: 'json' | 'log') => registry.exportTo(filePath, format),
  },

  ai: {
    enable:  (opts: { scope: string })    => ai.enable(opts.scope),
    disable: (opts: { scope: string })    => ai.disable(opts.scope),
    hints: {
      set:   (hash: string, hint: string) => ai.setHint(hash, hint),
      get:   (hash: string)               => ai.getHint(hash),
      clear: (hash: string)               => ai.clearHint(hash),
    },
  },
};

export default amend;
export { ScopeError, NetworkError, ValidationError };
export { Registry } from './registry/Registry.js';
export { AgentConfig } from './ai/AgentConfig.js';
export { amendHash } from './registry/hash.js';
