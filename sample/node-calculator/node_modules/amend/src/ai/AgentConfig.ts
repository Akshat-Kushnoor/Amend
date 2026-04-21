export class AgentConfig {
  private static instance: AgentConfig;

    private enabledScopes: Set<string> = new Set();
    private disabledScopes: Set<string> = new Set();
    private hintMap: Map<string, string> = new Map();

  private constructor() {}

  static getInstance(): AgentConfig {
    if (!AgentConfig.instance) {
      AgentConfig.instance = new AgentConfig();
    }
    return AgentConfig.instance;
  }

    enable(scope: string): void {
    this.enabledScopes.add(scope);
    this.disabledScopes.delete(scope);
  }

    disable(scope: string): void {
    this.disabledScopes.add(scope);
    this.enabledScopes.delete(scope);
  }

    isEnabled(filePath: string): boolean {
    for (const scope of this.disabledScopes) {
      if (filePath.startsWith(scope)) return false;
    }
    if (this.enabledScopes.size === 0) return true;
    for (const scope of this.enabledScopes) {
      if (filePath.startsWith(scope)) return true;
    }
    return false;
  }

    getEnabledScopes(): string[] {
    return [...this.enabledScopes];
  }

    getDisabledScopes(): string[] {
    return [...this.disabledScopes];
  }

    setHint(hash: string, hint: string): void {
    this.hintMap.set(hash, hint);
  }

    getHint(hash: string): string | undefined {
    return this.hintMap.get(hash);
  }

    clearHint(hash: string): void {
    this.hintMap.delete(hash);
  }

    getAllHints(): Record<string, string> {
    return Object.fromEntries(this.hintMap);
  }
}
