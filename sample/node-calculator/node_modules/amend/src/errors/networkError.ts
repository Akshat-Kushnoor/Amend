import { AmendError, AmendErrorOptions } from './AmendError.js';

export class NetworkError extends AmendError {
  constructor(message: string, options?: AmendErrorOptions) {
    super(message, 'NetworkError', options);
  }
}
