#!/usr/bin/env node

import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, copyFileSync } from 'node:fs';
import { join, dirname, resolve, relative } from 'node:path';
import { homedir } from 'node:os';
import { fileURLToPath } from 'node:url';

const CLAUDE_HOME = process.env.CLAUDE_HOME || join(homedir(), '.claude');
const PACKAGE_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const MANIFEST_FILE = join(CLAUDE_HOME, '.prompt-generator-manifest.json');
const PACKAGE_NAME = '@jl-cmd/prompt-generator';

const SKILLS = ['prompt-generator', 'agent-prompt'];

const HOOK_FILES = [
    'blocking/prompt_workflow_gate_config.py',
    'blocking/prompt_workflow_gate_core.py',
    'blocking/prompt_workflow_validate.py',
    'blocking/prompt_workflow_clipboard.py',
    'blocking/test_prompt_workflow_gate_core.py',
    'blocking/test_prompt_workflow_clipboard.py',
    'blocking/test_prompt_workflow_validate.py',
    'HOOK_SPECS_PROMPT_WORKFLOW.md',
];

const RULES = ['prompt-workflow-context-controls.md'];

function collectFiles(directory) {
    const collected = [];
    if (!existsSync(directory)) return collected;
    const entries = readdirSync(directory, { withFileTypes: true });
    for (const entry of entries) {
        const entryPath = join(directory, entry.name);
        if (entry.isDirectory()) {
            collected.push(...collectFiles(entryPath));
        } else {
            collected.push(entryPath);
        }
    }
    return collected;
}

function copyTree(sourceBase, destBase) {
    const files = collectFiles(sourceBase);
    const stats = { created: 0, updated: 0, paths: [] };
    for (const sourceFile of files) {
        const relativePath = relative(sourceBase, sourceFile);
        const destFile = join(destBase, relativePath);
        mkdirSync(dirname(destFile), { recursive: true });
        const existed = existsSync(destFile);
        copyFileSync(sourceFile, destFile);
        stats.paths.push(destFile);
        if (existed) {
            stats.updated++;
            console.log(`  \u21bb ${join(relative(CLAUDE_HOME, destBase), relativePath)} (updated)`);
        } else {
            stats.created++;
            console.log(`  \u2713 ${join(relative(CLAUDE_HOME, destBase), relativePath)} (new)`);
        }
    }
    return stats;
}

function writeManifest(installedFiles) {
    const manifest = { package: PACKAGE_NAME, version: '0.1.0', installedAt: new Date().toISOString(), files: installedFiles };
    writeFileSync(MANIFEST_FILE, JSON.stringify(manifest, null, 2) + '\n');
}

function install() {
    console.log(`\nInstalling ${PACKAGE_NAME}...\n`);
    mkdirSync(CLAUDE_HOME, { recursive: true });

    const allInstalledFiles = [];
    const summary = {};

    const skillsSource = join(PACKAGE_ROOT, 'skills');
    if (existsSync(skillsSource)) {
        let skillsCreated = 0;
        let skillsUpdated = 0;
        const skillPaths = [];
        for (const skillName of SKILLS) {
            const sourceDir = join(skillsSource, skillName);
            if (!existsSync(sourceDir)) continue;
            const stats = copyTree(sourceDir, join(CLAUDE_HOME, 'skills', skillName));
            skillsCreated += stats.created;
            skillsUpdated += stats.updated;
            skillPaths.push(...stats.paths);
        }
        summary.skills = { created: skillsCreated, updated: skillsUpdated };
        allInstalledFiles.push(...skillPaths);
    }

    const hooksSource = join(PACKAGE_ROOT, 'hooks');
    if (existsSync(hooksSource)) {
        let hooksCreated = 0;
        let hooksUpdated = 0;
        for (const hookFile of HOOK_FILES) {
            const sourcePath = join(hooksSource, hookFile);
            if (!existsSync(sourcePath)) continue;
            const destPath = join(CLAUDE_HOME, 'hooks', hookFile);
            mkdirSync(dirname(destPath), { recursive: true });
            const existed = existsSync(destPath);
            copyFileSync(sourcePath, destPath);
            allInstalledFiles.push(destPath);
            if (existed) { hooksUpdated++; } else { hooksCreated++; }
            console.log(`  ${existed ? '\u21bb' : '\u2713'} hooks/${hookFile} (${existed ? 'updated' : 'new'})`);
        }
        summary.hooks = { created: hooksCreated, updated: hooksUpdated };
    }

    const rulesSource = join(PACKAGE_ROOT, 'rules');
    if (existsSync(rulesSource)) {
        let rulesCreated = 0;
        let rulesUpdated = 0;
        for (const ruleFile of RULES) {
            const sourcePath = join(rulesSource, ruleFile);
            if (!existsSync(sourcePath)) continue;
            const destPath = join(CLAUDE_HOME, 'rules', ruleFile);
            mkdirSync(dirname(destPath), { recursive: true });
            const existed = existsSync(destPath);
            copyFileSync(sourcePath, destPath);
            allInstalledFiles.push(destPath);
            if (existed) { rulesUpdated++; } else { rulesCreated++; }
            console.log(`  ${existed ? '\u21bb' : '\u2713'} rules/${ruleFile} (${existed ? 'updated' : 'new'})`);
        }
        summary.rules = { created: rulesCreated, updated: rulesUpdated };
    }

    writeManifest(allInstalledFiles);

    console.log(`\nInstalled ${PACKAGE_NAME}:`);
    if (summary.skills) {
        const { created, updated } = summary.skills;
        console.log(`  skills: ${created + updated} files (${created} new, ${updated} updated)`);
    }
    if (summary.hooks) {
        const { created, updated } = summary.hooks;
        console.log(`  hooks: ${created + updated} files (${created} new, ${updated} updated)`);
    }
    if (summary.rules) {
        const { created, updated } = summary.rules;
        console.log(`  rules: ${created + updated} files (${created} new, ${updated} updated)`);
    }
    console.log('');
}

install();
