# main.py
from modes import DialogModes

def main():
    dialog = DialogModes(model="deepseek-r1")

    print("选择模式：1=单轮对话，2=多轮对话，3=严谨查询")
    mode = input("输入模式编号：").strip()

    while True:
        user_input = input("\n你：").strip()
        if user_input.lower() in ["exit", "quit"]:
            break

        # 是否展示模型“思考过程”
        show_thought = input("是否显示思考过程？(y/n)：").strip().lower() == "y"

        if mode == "1":
            reply = dialog.single_turn(user_input, show_thought=show_thought)
        elif mode == "2":
            reply = dialog.multi_turn(user_input, show_thought=show_thought)
        elif mode == "3":
            reply = dialog.strict_query(user_input, show_thought=show_thought)
        else:
            print("无效模式")
            continue

        print("助手：", reply.strip())

if __name__ == "__main__":
    main()
