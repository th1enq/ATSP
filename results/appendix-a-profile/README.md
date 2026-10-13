# Profiling Appendix A

Xem `docs/APPENDIX_A_PROFILE_2026-10-11.md`.

- `dense-original-ellipsoid.json`, `sparse-original-ellipsoid.json`: số đo trước tối ưu cập nhật ellipsoid.
- `dense.json`, `sparse.json`: số đo sau tối ưu; cap 400 vòng, cùng precision và cùng hash chuỗi điểm.
- `full-budget.json`: chẩn đoán sau tối ưu với ngân sách 30 giây; đọc trạng thái hoàn thành của từng truy vấn trước khi diễn giải thời gian.

Các số đo sử dụng terminal witness bên ngoài trên đồ thị hai đỉnh. Không phải benchmark ATSP và không chứng minh thuật toán tổng quát đã hoàn thành.

`dual-budget.json` ghi lần chạy sau bổ sung primal–dual: 63 query hoàn thành và chứng nhận của từng interval. Kiểm tra lại bằng `python3 scripts/check_sdp_value.py results/appendix-a-profile/dual-budget.json`. Xem `docs/SDP_DUAL_AUDIT_2026-10-11.md` để biết phạm vi cùng hướng và việc không còn dùng volume cutoff đơn lẻ để nâng cận dưới.

Mẫu nhiều hướng: `path-three-dual.json.gz` chứa 343 interval đã chứng nhận; `path-three-before-coupling.json.gz` và `path-three-before-inner.json.gz` lưu số đo lịch sử. Checker SDP đọc trực tiếp gzip. `triangle-three-diagnostic.json` là chẩn đoán incomplete với cap ellipsoid 0 trên mẫu không trực giao. Xem `docs/MULTI_DIRECTION_SDP_2026-10-11.md`.

## Nhánh generic không giao hoán

`noncommuting-barrier.json.gz`: 11 khoảng primal–dual, gồm accuracy 1/8, 1e-12, 1e-30 và tám truy vấn của signing Appendix A trên hai ray không giao hoán.

`triangle-three-barrier.json.gz`: 42 khoảng có chứng nhận, hoàn thành một bước Appendix A trên tam giác, khoảng 207,392 giây. Không dùng inner ellipsoid. Ở bản profiler tạo file này, trường `feasibility_calls` ghi Newton steps; bản mã mới tách `newton_steps` riêng. Các mốc trước giữ nguyên.

Phát lại độc lập:

```sh
python3 scripts/check_sdp_value.py results/appendix-a-profile/noncommuting-barrier.json.gz
python3 scripts/check_sdp_value.py results/appendix-a-profile/triangle-three-barrier.json.gz
```
