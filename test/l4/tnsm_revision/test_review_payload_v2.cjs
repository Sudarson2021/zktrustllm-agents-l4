const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../../..');
const workflow = JSON.parse(fs.readFileSync(path.join(root, 'workflows/n8n/tnsm_revision/L4FinalPaperReviewV2.json'), 'utf8'));
const code = workflow.nodes.find(n => n.id === 'validate-review').parameters.jsCode;
const validate = new Function('$json', code);
const input = {run_id: 'run-1', reviewer_id: 'reviewer-1', reviewer_role: 'mno_approver', approved: false};
assert.equal(validate(input)[0].json.approved, false);
assert.equal(validate({body: {...input, approved: true}})[0].json.approved, true);
let rejected = 0;
for (const approved of ['false', 'true', 0, 1, null, {}, []]) {
  assert.throws(() => validate({...input, approved}), /Boolean/); rejected++;
}
for (const bad of [{...input, run_id: ''}, {...input, reviewer_id: {}}, {...input, reviewer_role: null}, {...input, rationale: false}, []]) {
  assert.throws(() => validate(bad)); rejected++;
}
assert.equal(workflow.active, false);
assert.equal(workflow.nodes.find(n => n.id === 'review-hook').parameters.path, 'tnsm-action-review-v2');
console.log(`PASS strict review payload: 2 valid branches and ${rejected} malformed inputs; inactive export`);
