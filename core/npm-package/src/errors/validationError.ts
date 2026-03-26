import { AmendError, AmendErrorOptions } from './AmendError.js';

export class ValidationError extends AmendError {
  constructor(message: string, options?: AmendErrorOptions) {
    super(message, 'ValidationError', options);
  }
}
