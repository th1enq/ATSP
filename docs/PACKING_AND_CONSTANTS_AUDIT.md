# Kiểm toán packing cây và các hằng số còn thiếu

**Ngày:** 2026-10-08. Nguồn chính: [A polynomial-time construction of strong thin trees](https://github.com/openai/math/blob/main/preprints/A-polynomial-time-construction-of-strong-thin-trees-September-23-2026/paper.pdf), đặc biệt Mục 2, 3, 5 và 6. Thuật toán matroid union dùng đặc tả đồ thị trao đổi trong [Matroid optimization in auction theory, §4.4.1](https://publications.rwth-aachen.de/record/1023729/files/1023729.pdf).

## Mốc 3: phần packing đã cài

`scripts/tree_packing.py` nhận chứng chỉ nén của `scripts/certify_compress.py`, mở rộng tối đa `n⁴−1` bản sao rồi chạy graphic matroid union cho số cây `q` yêu cầu. Mỗi màu chứa một rừng. Tại mỗi vòng, chương trình tạo cung trao đổi `e→f` khi thay cạnh `e` của rừng bằng `f` vẫn giữ rừng, và đánh dấu `f` nếu có thể thêm trực tiếp. BFS tìm đường tăng ngắn nhất từ cạnh thêm được tới cạnh chưa dùng. Một vòng tăng thêm đúng một cạnh vào hợp các rừng. Nếu đạt `q(n−1)` cạnh, mỗi rừng là cây bao.

Nếu không còn đường tăng, lấy `R` là các cạnh đạt tới được từ nguồn BFS. Chương trình chia đỉnh thành các thành phần của đồ thị gồm các cạnh ngoài `R`. Cạnh đi qua phân hoạch này nằm trong `R`; bất đẳng thức `|E(P)|<q(|P|−1)` được kiểm tra trực tiếp rồi xuất làm chứng chỉ không thể packing đủ `q` cây. Khi `q(n−1)>m`, phân hoạch các đỉnh đơn lẻ là chứng chỉ tức thời. `--verify` kiểm tra lại chứng chỉ thành công hoặc thất bại từ tệp JSON, độc lập với các bước tăng.

Với `q(n−1)≤m`, có nhiều nhất `m` vòng tăng. Mỗi vòng duyệt hữu hạn `q` rừng, `m` cạnh và tìm đường trong rừng; số phép toán là đa thức theo `n,m,q`, và `q≤m/(n−1)`. Mã hiện ưu tiên tính đúng và chứng chỉ; việc dựng lại toàn bộ đồ thị trao đổi ở mỗi vòng sẽ chậm khi `m` gần `n⁴`.

Kiểm thử so quyết định packing với công thức Nash–Williams–Tutte trên toàn bộ `3^6=729` đa đồ thị 4 đỉnh có bội số mỗi cặp từ 0 đến 2, cùng 60 đa đồ thị ngẫu nhiên `n=2..5`; từng cây hoặc phân hoạch đầu ra đều được kiểm tra. Đồ thị nén từ witness 6 đỉnh cho `18` cây bao rời cạnh, mỗi cây `5` cạnh. Đây là phép kiểm chứng thuật toán packing, không chứng minh cây nào trong số đó có độ mỏng `C/k`.

**Chưa qua toàn bộ Mốc 3:** Lemma 3.3 yêu cầu oracle tách cho trọng số hữu tỉ bất kỳ `z_e`, theo LP (3.18). `scripts/weighted_partition_oracle.py` đã có oracle MST hữu tỉ của LP và bộ liệt kê phân hoạch nhỏ làm đối chứng; bộ packing ở đây xử lý trường hợp trọng số đơn vị. Bộ liệt kê phân hoạch có thời gian mũ. Cần thêm một LP hữu tỉ đa thức hoặc ellipsoid chính xác có chứng chỉ trước khi triển khai Proposition 3.1.

Một thành phần độc lập của Mốc 4 cũng đã có: `scripts/exact_psd.py` kiểm tra ma trận đối xứng hữu tỉ là PSD bằng khử Schur chính xác, hoặc trả vector hữu tỉ có dạng toàn phương âm. Các ca Gram ngẫu nhiên và ma trận bất định đã được kiểm thử. Nó chưa giải bài toán tối ưu ma trận của Proposition 3.1.

## Mốc 0: bảng tham số thực thi

| Thành phần bản thảo | Giá trị hoặc điều kiện tìm được | Trạng thái cho mã |
|---|---|---|
| Theorem 2.1 | `h≥h0`; Mục 2.4 chọn `h0` sao cho nhiều bất đẳng thức dạng `O(h^{-a}(1+log h)^b)` đạt ngưỡng | Có cận đủ có điều kiện `h0=2^4096` từ Lemma 2.4; xem `EXPLICIT_THRESHOLD_AUDIT.md`. Chưa kiểm toán độc lập chứng minh hình học của bổ đề. |
| Proposition 3.1 | `A,r0` tuyệt đối; continuation dùng `κ=1/(m+1)`, `t=κ/32`, `g` dyadic trong `[r^{-1/8},2r^{-1/8}]` | Có ứng viên có điều kiện `A=12,r0=2^4097` từ phép đếm continuation; Lemmas 3.2–3.4 chưa kiểm toán độc lập. |
| Lemma 3.3 | LP hữu tỉ (3.18), oracle MST chính xác | MST hữu tỉ đã cài; LP/ellipsoid hữu tỉ chưa có, packing đơn vị không thay thế được |
| Lemma 3.4 | Bán kính trong/ngoài và lưới hữu tỉ phụ thuộc `P=n+m+2` | PSD hữu tỉ đã cài riêng; chưa kiểm toán hết độ dài bit, chưa cài ellipsoid |
| Lemma 4.1 | Chuẩn hóa khung vector với sai số hữu tỉ | Các điều kiện ngưỡng hiển thị thỏa khi `r≥2`; chưa cài và chưa kiểm toán hết cận precision. |
| Lemma 5.2 | Có thể lấy `Cs=2^20` theo cuối Mục 5 | Các bất đẳng thức ngưỡng thỏa khi `r≥2`; thuật toán ký dấu Appendix A chưa cài. |
| Lemma 6.1 | Dùng `r≥R0`, `r/4≤r'≤r/2`, `ar=1/2+3Cs r^{-1/8}` và `ar/(r'/r)≤1+C1 r^{-1/16}` | Ứng viên có điều kiện `R0=2^4097`, `C1=26388516044836`; xem `EXPLICIT_THRESHOLD_AUDIT.md`. |
| Theorem 1.1 | Với đồ thị tường minh, `rinit≥k/3` và dừng ở `rJ<R0`; nén bội số nhân thêm hệ số 2 | Cận có điều kiện `C_binary=12·2^4097`; chưa có đường mã thực thi đầy đủ. |

Từ phép nhân tỉ số ở Mục 6, nếu sau này xác lập được `R0≥1` và `C1≥0`, một cận ký hiệu an toàn cho trường hợp bội số nhị phân là

`C_binary ≤ 6 R0 exp(C1 R0^{-1/16}/(1−2^{-1/16}))`.

Lý do: `rinit≥k/3`, `rJ<R0`; đọc các tham số trước bước cuối theo chiều ngược cho `r_i≥R0·2^{J−1−i}`, nên `sum_i r_i^{-1/16}≤R0^{-1/16}/(1−2^{-1/16})`. Dùng `1+x≤exp(x)` và hệ số 2 của phép nén. Đây là **cận điều kiện**, không phải hằng số triển khai vì `R0,C1` vẫn chưa lượng hóa.

[Danh mục Lean của OpenAI Math](https://github.com/openai/math/blob/main/lean/formalization.yaml) liệt kê bài tồn tại strong thin tree; tại thời điểm kiểm tra, danh mục không liệt kê bản thảo dựng cây như một kết quả chính đã formalize. Điều này không chứng minh mã Lean không chứa thành phần liên quan, nhưng không thể dùng danh mục ấy làm xác nhận tự động cho các bước thuật toán và bit complexity.
