# Kiểm tra backend nguồn

Các JSON được xuất bằng `scripts/general_sparsification.py`; chạy lại:

```sh
python3 scripts/general_sparsification.py verify results/general-sparsification/source-small-branch.json
python3 scripts/general_sparsification.py verify results/general-sparsification/continuation-prefix.json
python3 scripts/general_sparsification.py verify results/general-sparsification/appendix-a-budget.json
```

`below-source-cutoff` là nhánh dừng 0 vòng. `incomplete` chỉ chứng nhận prefix đã lưu, không chứng nhận sparsification thành công hoặc vô nghiệm. Thử nghiệm Appendix A nhận terminal witness bên ngoài, không phải output continuation. Xem `docs/GENERAL_SPARSIFICATION_2026-10-11.md` để biết nguồn, lệnh và giới hạn.

`appendix-a-dual.json` là kết quả mới sau khi bổ sung chứng nhận đối ngẫu: hoàn thành một bước trên terminal witness được cung cấp, `r=8 -> 3`. Không phải kết quả continuation từ trạng thái khởi đầu. Cut bound theo epsilon nguồn vẫn rất lỏng trên mẫu nhỏ. Chi tiết: `docs/SDP_DUAL_AUDIT_2026-10-11.md`.

`path-three-dual.json`: bước hoàn chỉnh `r=8 -> 3` trên đồ thị ba đỉnh/hai hướng trực giao, terminal witness cung cấp sẵn. `triangle-three-diagnostic.json`: mẫu không trực giao dừng incomplete với cap ellipsoid 0; không phải chứng minh vô nghiệm. Xem `docs/MULTI_DIRECTION_SDP_2026-10-11.md`.

## Mốc SDP không giao hoán và continuation từ đầu

- `triangle-three-barrier.json`: một bước bằng Appendix A + SDP không giao hoán, terminal witness được cung cấp; giữ 7 cạnh, packing 3 cây. Có 42 chứng nhận SDP trong `../appendix-a-profile/triangle-three-barrier.json.gz`.
- `path-three-from-initial.json`: chạy từ trạng thái ban đầu, `g=1/64`, dùng Appendix A; packing 8→3.
- `triangle-three-from-initial.json`: chạy từ trạng thái ban đầu, 972 response, `g=1/64`; signing ứng viên được kiểm tra trực tiếp, không phải descent Appendix A; packing 8→3.

Các origin từ đầu là `instance-parameter-continuation`, không đổi thành `source-initial-state`. Các file lịch sử vẫn được giữ nguyên. Xem `docs/GENERAL_COMPLETION_2026-10-11.md`.

`triangle-three-tree.json`: cây cuối từ trạng thái khởi đầu, chế độ instance tự chọn `g=1/32`, 972 response, ký dấu Appendix A, packing 8→3. Cây ID `[1,8]` tương ứng `0–1`, `1–2`; cut ratio bound đối với đa đồ thị đầu vào là `1/4`. Replay bằng `python3 scripts/general_tree.py verify results/general-sparsification/triangle-three-tree.json`.
