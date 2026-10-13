# Đo và tối ưu oracle Appendix A — 2026-10-11

## Đã xác định được điều gì

CProfile 20 giây trên terminal witness của đồ thị hai đỉnh, tám cạnh song song cho thấy quá trình bị dừng **ngay truy vấn potential đầu tiên**. Sau extraction, union có bảy cây; potential nhận bảy biến và ma trận 2×2. SDP có bảy biến thực.

Ở lần đo trước tối ưu, có khoảng 1.519 lần gọi separator trong 20 giây có cProfile. Riêng các hàm tính phân số chiếm phần lớn chi phí; separator và phép cập nhật ellipsoid cùng là điểm nghẽn. CProfile có overhead nên các thời gian này không được coi là thời gian chạy bình thường.

Phép đo có instrument riêng xác nhận truy vấn potential đầu tiên yêu cầu accuracy **1/4**, truy vấn SDP bên trong yêu cầu **1/8**. Inner radius vẫn là `1/80000000000`, tâm ellipsoid đã có mẫu số đến 89 bit. Như vậy việc giải thích độ chậm chỉ bằng precision cực nhỏ của finite difference là chưa đầy đủ: quá trình hiện còn chậm trước khi đi tới pha đó.

## Thay đổi mã

1. **Separator SDP:** biên dịch trước các hệ số khác 0 của LMI; chỉ tính nửa ma trận đối xứng. Cut vẫn được tính chính xác bằng witness hữu tỉ, bỏ phép nhân hệ số 0.
2. **Ellipsoid:** đưa hằng số ra ngoài vòng lặp; chia vector rank-one một lần thay vì chia cho từng phần tử; cập nhật nửa ma trận rồi đối xứng. Tất cả vẫn dùng `Fraction`, cùng grid và inflation. Không giảm precision.
3. **Sửa xử lý giới hạn vòng:** bổ sung `IterationLimitReached` và `VolumeCutoffReached`. Trước đây `max_iterations` do người chạy đặt có thể kết thúc bằng cùng thông báo volume cutoff và bị SDP dùng để nâng cận dưới. Nay operational cap không được biến thành kết luận volume hoặc cận dưới SDP.
4. **Ngân sách bên trong:** truyền `--sdp-iteration-cap` và `--value-query-cap` qua toàn bộ luồng ký dấu. Cap ngoài `--signing-cap` chỉ giới hạn bước descent, không đủ để giới hạn công việc bên trong một truy vấn.
5. **Công cụ đo:** `benchmarks/profile_appendix_a.py` lưu thời gian potential/SDP/ellipsoid, số vòng, precision, độ dài bit, trạng thái hoàn thành và hash chuỗi các điểm/target SDP. Có tùy chọn xuất cProfile.

`VolumeCutoffReached` vẫn chỉ có ý nghĩa theo inner-ball/weak-optimization promise của nguồn. Các promise ấy chưa được kiểm toán độc lập đầy đủ; thay đổi này xử lý lỗi nhầm ngân sách, không tự chứng minh toàn bộ oracle SDP.

## So sánh cùng lượng công việc

Bốn lần chạy đều có cap **400 cập nhật ellipsoid**, 401 lần kiểm tra tâm, 402 lần gọi separator kể cả reference point. Tất cả đều dừng bằng `IterationLimitReached`. Chuỗi điểm/target có cùng SHA-256:

`de4e93093680568ee07c567c3744de0351bd6de2ba17f595ee94926076da752c`

| Phiên bản | Tổng thời gian | Trong separator |
|---|---:|---:|
| Separator dense, ellipsoid trước tối ưu | 2,661 s | 0,887 s |
| Separator sparse, ellipsoid trước tối ưu | 2,216 s | 0,466 s |
| Separator dense, ellipsoid đã tối ưu | 1,666 s | 0,816 s |
| Separator sparse, ellipsoid đã tối ưu | 1,299 s | 0,438 s |

So lần đầu và lần cuối: thời gian giảm khoảng **51%**, tương đương khoảng **2 lần** trên công việc cố định này. Đây là một lần đo cho mỗi phiên bản, không phải thống kê nhiều lần, tốc độ trên TSPLIB hay tốc độ hoàn thành toàn bộ thuật toán. Dense trong công cụ đo là công thức separator cũ dành cho đối chiếu; production dùng sparse.

Dữ liệu: `results/appendix-a-profile/*original-ellipsoid.json`, `dense.json`, `sparse.json`. Các file `original-ellipsoid` lưu số đo lịch sử trước khi thay đổi cập nhật ellipsoid; chạy lại công cụ hiện tại dùng ellipsoid đã tối ưu.

## Chạy lại

```sh
python3 benchmarks/profile_appendix_a.py --separator dense \
  --iteration-cap 400 --seconds 30 --output /tmp/dense.json
python3 benchmarks/profile_appendix_a.py --separator sparse \
  --iteration-cap 400 --seconds 30 --output /tmp/sparse.json
```

Chạy luồng mới với giới hạn bên trong:

```sh
python3 scripts/general_sparsification.py step \
  instances/general-sparsification/parallel-eight.json \
  --terminal-witness instances/general-sparsification/parallel-eight-terminal.json \
  --sdp-iteration-cap 400 --value-query-cap 20 --seconds 30 \
  --output /tmp/appendix-budget.json
```

Terminal witness vẫn là dữ liệu cung cấp bên ngoài đã kiểm tra, không phải kết quả continuation. `incomplete` không phải ký dấu hoặc sparsification thành công.

## Kiểm tra

Các test mới xác nhận cap không trở thành lower bound SDP; separator sparse trả đúng cut dense trên các điểm hữu tỉ; và luồng tổng quát ghi nhận cap SDP là `incomplete`. Test scalar SDP vẫn bao khoảng nghiệm thật và kiểm tra witness feasible.

Bộ kiểm tra toàn repo được chạy lại sau thay đổi phần ellipsoid dùng chung. Kết quả được bổ sung dưới đây cùng lần chạy 30 giây sau tối ưu.

## Kết quả sau tối ưu

- Toàn bộ 71 test qua; 1 test LP/SciPy bỏ qua vì thiếu phụ thuộc tùy chọn. Lần chạy cuối diễn ra sau thay đổi ellipsoid, mất 12,359 giây.
- Lần đo 30 giây sau tối ưu, không chạy test đồng thời, vẫn dừng ở **truy vấn potential đầu tiên** (`accuracy=1/4`, SDP `accuracy=1/8`). Có 8.134 lần gọi separator.
- Trong truy vấn đó đã bắt đầu **5 lần giải feasibility ellipsoid**: 3 trả về điểm feasible, 1 dừng theo volume/collapse condition của oracle, 1 bị ngắt bởi ngân sách thời gian. Các lần trả feasible đã được separator kiểm tra; toàn bộ interval potential vẫn chưa hoàn thành.
- Riêng lần dừng theo volume/collapse mất khoảng **13,887 giây**, là lần inner solve hoàn tất tốn thời gian nhất. Kiểm tra feasible ở các target khác mất khoảng 2–3 giây. Separator chiếm tổng khoảng 10,799 giây trong ngân sách 30 giây; phần còn lại chủ yếu vẫn là cập nhật ellipsoid/số hữu tỉ.

Dữ liệu chi tiết: `results/appendix-a-profile/full-budget.json`. Giới hạn 100.000 vòng do công cụ đặt không kéo dài quá cutoff nguồn: `find_feasible` lấy min với volume iteration limit nội bộ. Ý nghĩa toán học của volume/collapse còn phụ thuộc ball promise đã nêu.

**Chưa có ký dấu hoàn chỉnh hay một bước general sparsification thành công.** Cải thiện khoảng 2 lần ở công việc cố định chưa đủ giải quyết việc một potential query phải chạy nhiều inner solve. Hướng tối ưu tiếp có căn cứ là bổ sung các cận/dual witness chính xác để bỏ sớm target không đạt, hoặc giảm số lần giải feasibility trong weak optimization; mỗi cận mới cần được chứng nhận trước khi dùng cập nhật interval. Việc giảm precision tùy ý sẽ làm mất bảo đảm của oracle.

## Cập nhật sau bổ sung đối ngẫu

Các số đo và nhận xét chưa hoàn thành ở trên là trước khi bổ sung primal–dual certificates. Cùng terminal witness nay chạy xong trong 1,510 giây, với 63 interval SDP được kiểm tra độc lập; cấu trúc cùng hướng giúp không cần ellipsoid. Xem [SDP_DUAL_AUDIT_2026-10-11.md](SDP_DUAL_AUDIT_2026-10-11.md) để biết chứng minh, dữ liệu và giới hạn phạm vi.
