/**
 * ESLint Configuration for Nano Banana Studio Pro
 * ================================================
 * Enforces consistent coding standards across the codebase.
 */

module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
  },
  plugins: ['react', 'react-hooks'],
  rules: {
    // Error Prevention
    'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    'no-console': ['warn', { allow: ['warn', 'error', 'info'] }],
    'no-debugger': 'error',
    'no-duplicate-imports': 'error',
    'no-template-curly-in-string': 'warn',
    
    // Best Practices
    'eqeqeq': ['error', 'always', { null: 'ignore' }],
    'no-eval': 'error',
    'no-implied-eval': 'error',
    'no-return-await': 'warn',
    'require-await': 'warn',
    
    // React Specific
    'react/jsx-uses-react': 'error',
    'react/jsx-uses-vars': 'error',
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    
    // Event Handler Best Practices
    'react/jsx-no-bind': ['warn', {
      allowArrowFunctions: true,
      allowFunctions: false,
      allowBind: false,
    }],
    
    // Code Style
    'semi': ['error', 'never'],
    'quotes': ['warn', 'single', { avoidEscape: true }],
    'indent': ['warn', 2, { SwitchCase: 1 }],
    'comma-dangle': ['warn', 'always-multiline'],
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
  overrides: [
    {
      files: ['*.jsx', '*.tsx'],
      rules: {
        'react/prop-types': 'off',
      },
    },
  ],
}
