import { AmendError, AmendErrorOptions } from './AmendError.js';

export class ScopeError extends AmendError {
  constructor(message: string, options?: AmendErrorOptions) {
    super(message, 'ScopeError', options);
  }
}
