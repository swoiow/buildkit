# BuildPlan Examples / BuildPlan 示例

按难度从简单到复杂：
Ordered from simple to advanced:

1. `docs/examples/01-minimal.md`
2. `docs/examples/02-release.md`
3. `docs/examples/03-temp-build-assets.md`

Note:
通配包名（如 `mypkg.*`）会自动展开为真实包列表，排除子包请用 `exclude_packages`。
Wildcard package names like `mypkg.*` are expanded automatically; use `exclude_packages` to drop subpackages.

命名空间包请启用 `options.use_namespace_packages = True`。
For namespace packages, enable `options.use_namespace_packages = True`.
