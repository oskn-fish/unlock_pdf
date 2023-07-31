import argparse
import os
import string
import itertools
import ray
ray.init()
import math
import pypdf


from logging import getLogger, DEBUG, StreamHandler
logger = getLogger()
logger.setLevel(DEBUG)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.addHandler(handler)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path")
    parser.add_argument("-o", "--output_path")
    parser.add_argument("-w","--worker_num")
    args = parser.parse_args()
    return args


@ray.remote
def try_decypt(doc: pypdf.PdfReader, password_list: list, output_path: str):
    for password in password_list:
        value = doc.decrypt(password)
        if value > 0:
            doc.write(output_path)
            print(f"the password was {password}: unlocked file is saved to {output_path}")

            
            
def set_default_args(args):
    input_path = args.input_path
    
    if not args.output_path:
        to_ext, ext = os.path.splitext(args.input_path)
        output_path = to_ext+"_unlocked"+ext
    else:
        output_path = args.output_path
        
    if not args.worker_num:
        worker_num = 5
    else:
        worker_num = args.worker_num
        
    return input_path, output_path, worker_num
    

def main():
    
    args = get_args()
    input_path, output_path, worker_num = set_default_args(args)
    #http://www.otupy.net/archives/36058318.html
    chars = string.ascii_letters+string.digits+string.punctuation
    doc = pypdf.PdfReader(input_path)
    

    for i in range(1,100):
        print(f"trying passwords with length {i} ...")
        
        password_list = list(map(lambda x: "".join(x), list(itertools.product(chars, repeat=i))))
        password_num = len(password_list)
        passwords_per_worker = math.ceil(password_num/worker_num)
        passwords_for_worker = [password_list[idx:idx+passwords_per_worker+1] for idx in range(0,password_num, passwords_per_worker)]
        passwords_for_worker.append(password_list[passwords_per_worker*worker_num:password_num+1])
        
        objectIDs = [try_decypt.remote(doc, passwords_per_worker, output_path) for passwords_per_worker in passwords_for_worker]
        ray.get(objectIDs)


if __name__ == "__main__":
    main()