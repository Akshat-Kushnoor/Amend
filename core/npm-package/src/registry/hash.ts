import { createHash } from 'crypto';

export function seg(input: string): string {
  const bytes = createHash('sha256').update(input, 'utf8').digest();
  return bytes.readUInt32BE(0).toString(36).padStart(7, '0').slice(0, 5);
}

export function amendHash(
  filePath: string,
  line: number,
  className: string,
  funcName: string,
  message: string,
  errorClass: string,
): string {
  const location  = seg(`${filePath}:${line}`);
  const structure = seg(`${className}.${funcName}`);
  const instance  = seg(`${message}|${errorClass}`);
  return `${location}-${structure}-${instance}`;
}
